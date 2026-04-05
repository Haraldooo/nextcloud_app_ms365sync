<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Service;

use OCA\Ms365Sync\Db\SyncJob;
use OCA\Ms365Sync\Db\SyncJobMapper;
use OC\Authentication\Token\IProvider as ITokenProvider;
use OC\Authentication\Token\IToken;
use OCP\IUserSession;
use OCP\Security\ISecureRandom;
use Psr\Log\LoggerInterface;

class SyncJobService {
    public function __construct(
        private SyncJobMapper $mapper,
        private RcloneApiService $rcloneApi,
        private SettingsService $settingsService,
        private MicrosoftGraphService $graphService,
        private ITokenProvider $tokenProvider,
        private IUserSession $userSession,
        private ISecureRandom $secureRandom,
        private LoggerInterface $logger,
    ) {
    }

    /**
     * @return SyncJob[]
     */
    public function listJobs(): array {
        return $this->mapper->findAll();
    }

    public function getJob(int $id): SyncJob {
        return $this->mapper->findById($id);
    }

    public function createJob(
        int $tenantId,
        string $name,
        string $sourceType,
        ?string $sourceSiteId,
        string $sourceDriveId,
        string $sourceDriveName,
        string $destType,
        string $destPath,
        ?string $destUser,
        string $syncMode = 'copy',
        string $schedule = 'manual',
    ): SyncJob {
        $job = new SyncJob();
        $job->setTenantId($tenantId);
        $job->setName($name);
        $job->setSourceType($sourceType);
        $job->setSourceSiteId($sourceSiteId);
        $job->setSourceDriveId($sourceDriveId);
        $job->setSourceDriveName($sourceDriveName);
        $job->setDestType($destType);
        $job->setDestPath($destPath);
        $job->setDestUser($destUser);
        $job->setSyncMode($syncMode);
        $job->setSchedule($schedule);
        $job->setStatus('idle');
        $now = new \DateTime();
        $job->setCreatedAt($now);
        $job->setUpdatedAt($now);
        return $this->mapper->insert($job);
    }

    public function updateJob(int $id, array $data): SyncJob {
        $job = $this->mapper->findById($id);

        foreach (['name', 'destType', 'destPath', 'destUser', 'syncMode', 'schedule'] as $field) {
            if (isset($data[$field])) {
                $setter = 'set' . ucfirst($field);
                $job->$setter($data[$field]);
            }
        }
        if (isset($data['enabled'])) {
            $job->setEnabled((bool)$data['enabled']);
        }

        $job->setUpdatedAt(new \DateTime());
        return $this->mapper->update($job);
    }

    public function deleteJob(int $id): void {
        $job = $this->mapper->findById($id);
        if ($job->getStatus() === 'running' && $job->getRcloneJobId() !== null) {
            try {
                $this->rcloneApi->stopJob($job->getRcloneJobId());
            } catch (\Exception $e) {
                $this->logger->warning('Failed to stop rclone job before deletion: ' . $e->getMessage());
            }
        }
        $this->revokeJobToken($job);
        $this->mapper->delete($job);
    }

    public function startJob(int $id): SyncJob {
        $job = $this->mapper->findById($id);
        $tenant = $this->settingsService->getTenant($job->getTenantId());
        $secret = $this->settingsService->getDecryptedSecret($tenant);

        // Determine which NC user to write files as
        $destUser = $job->getDestUser();
        if (!$destUser) {
            $user = $this->userSession->getUser();
            if ($user === null) {
                throw new \RuntimeException('No destination user set and no user logged in');
            }
            $destUser = $user->getUID();
        }

        // Generate a temporary app password for the rclone container
        // This reuses the user's NC session/permissions — no manual config needed
        $appPassword = $this->secureRandom->generate(72, ISecureRandom::CHAR_ALPHANUMERIC);
        $token = $this->tokenProvider->generateToken(
            $appPassword,
            $destUser,
            $destUser,
            null,
            'ms365sync-job-' . $job->getId(),
            IToken::PERMANENT_TOKEN,
            IToken::DO_NOT_REMEMBER,
        );

        // Build rclone job config
        $jobConfig = [
            'job_id' => $job->getId(),
            'tenant_id' => $tenant->getTenantId(),
            'client_id' => $tenant->getClientId(),
            'client_secret' => $secret,
            'drive_id' => $job->getSourceDriveId(),
            'source_type' => $job->getSourceType(),
            'dest_path' => $job->getDestPath(),
            'dest_user' => $destUser,
            'sync_mode' => $job->getSyncMode(),
            'nextcloud_url' => $this->settingsService->getNextcloudUrl(),
            'nextcloud_app_password' => $appPassword,
        ];

        $rcloneJobId = $this->rcloneApi->startJob($jobConfig);

        $job->setStatus('running');
        $job->setRcloneJobId($rcloneJobId);
        $job->setNcTokenId($token->getId());
        $job->setDestUser($destUser);
        $job->setLastRunAt(new \DateTime());
        $job->setLastError(null);
        $job->setBytesTransferred(0);
        $job->setFilesTransferred(0);
        $job->setUpdatedAt(new \DateTime());

        return $this->mapper->update($job);
    }

    public function stopJob(int $id): SyncJob {
        $job = $this->mapper->findById($id);

        if ($job->getRcloneJobId() !== null) {
            try {
                $this->rcloneApi->stopJob($job->getRcloneJobId());
            } catch (\Exception $e) {
                $this->logger->warning('Failed to stop rclone job: ' . $e->getMessage());
            }
        }

        $this->revokeJobToken($job);

        $job->setStatus('paused');
        $job->setRcloneJobId(null);
        $job->setNcTokenId(null);
        $job->setUpdatedAt(new \DateTime());

        return $this->mapper->update($job);
    }

    public function getProgress(int $id): array {
        $job = $this->mapper->findById($id);

        if ($job->getRcloneJobId() === null) {
            return [
                'status' => $job->getStatus(),
                'bytesTransferred' => $job->getBytesTransferred(),
                'filesTransferred' => $job->getFilesTransferred(),
            ];
        }

        try {
            $status = $this->rcloneApi->getJobStatus($job->getRcloneJobId());

            // Update job with latest stats
            $job->setBytesTransferred((int)($status['bytes'] ?? 0));
            $job->setFilesTransferred((int)($status['files'] ?? 0));

            if (($status['finished'] ?? false) === true) {
                $job->setStatus(empty($status['error']) ? 'completed' : 'error');
                $job->setLastError($status['error'] ?? null);
                $job->setRcloneJobId(null);
                $this->revokeJobToken($job);
                $job->setNcTokenId(null);
            }

            $job->setUpdatedAt(new \DateTime());
            $this->mapper->update($job);

            return array_merge($status, [
                'status' => $job->getStatus(),
                'bytesTransferred' => $job->getBytesTransferred(),
                'filesTransferred' => $job->getFilesTransferred(),
            ]);
        } catch (\Exception $e) {
            return [
                'status' => $job->getStatus(),
                'bytesTransferred' => $job->getBytesTransferred(),
                'filesTransferred' => $job->getFilesTransferred(),
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * @return SyncJob[]
     */
    public function findRunningJobs(): array {
        return $this->mapper->findByStatus('running');
    }

    /**
     * Revoke the temporary app password created for the rclone container.
     */
    private function revokeJobToken(SyncJob $job): void {
        $tokenId = $job->getNcTokenId();
        if ($tokenId === null) {
            return;
        }
        try {
            $this->tokenProvider->invalidateTokenById(
                $job->getDestUser(),
                $tokenId,
            );
            $this->logger->info('Revoked app token for job ' . $job->getId());
        } catch (\Exception $e) {
            $this->logger->warning('Failed to revoke app token for job ' . $job->getId() . ': ' . $e->getMessage());
        }
    }
}
