<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Service;

use OCP\Http\Client\IClientService;
use Psr\Log\LoggerInterface;

class RcloneApiService {
    public function __construct(
        private IClientService $clientService,
        private SettingsService $settingsService,
        private LoggerInterface $logger,
    ) {
    }

    private function getBaseUrl(): string {
        return rtrim($this->settingsService->getContainerUrl(), '/');
    }

    public function healthCheck(): bool {
        try {
            $client = $this->clientService->newClient();
            $response = $client->get($this->getBaseUrl() . '/health', [
                'timeout' => 5,
            ]);
            $data = json_decode($response->getBody(), true);
            return ($data['status'] ?? '') === 'ok';
        } catch (\Exception $e) {
            $this->logger->warning('Rclone container health check failed: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * Start a sync job in the rclone container.
     *
     * @return int rclone job ID
     */
    public function startJob(array $jobConfig): int {
        $client = $this->clientService->newClient();
        $response = $client->post($this->getBaseUrl() . '/jobs/start', [
            'json' => $jobConfig,
            'timeout' => 30,
        ]);

        $data = json_decode($response->getBody(), true);
        return (int)$data['jobid'];
    }

    public function stopJob(int $rcloneJobId): void {
        $client = $this->clientService->newClient();
        $client->post($this->getBaseUrl() . '/jobs/stop', [
            'json' => ['jobid' => $rcloneJobId],
            'timeout' => 10,
        ]);
    }

    public function getJobStatus(int $rcloneJobId): array {
        $client = $this->clientService->newClient();
        $response = $client->get($this->getBaseUrl() . '/jobs/' . $rcloneJobId . '/status', [
            'timeout' => 10,
        ]);
        return json_decode($response->getBody(), true);
    }

    public function getJobLog(int $jobId, int $lines = 100): string {
        $client = $this->clientService->newClient();
        $response = $client->get($this->getBaseUrl() . '/jobs/' . $jobId . '/log', [
            'query' => ['lines' => $lines],
            'timeout' => 10,
        ]);
        return $response->getBody();
    }
}
