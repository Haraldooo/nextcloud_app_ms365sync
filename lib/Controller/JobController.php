<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Controller;

use OCA\Ms365Sync\AppInfo\Application;
use OCA\Ms365Sync\Service\SyncJobService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class JobController extends Controller {
    public function __construct(
        IRequest $request,
        private SyncJobService $syncJobService,
    ) {
        parent::__construct(Application::APP_ID, $request);
    }

    /**
     * @NoAdminRequired
     */
    public function list(): JSONResponse {
        return new JSONResponse($this->syncJobService->listJobs());
    }

    /**
     * @NoAdminRequired
     */
    public function get(int $id): JSONResponse {
        try {
            return new JSONResponse($this->syncJobService->getJob($id));
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Job not found'], Http::STATUS_NOT_FOUND);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function create(
        int $tenantId,
        string $name,
        string $sourceType,
        ?string $sourceSiteId,
        string $sourceDriveId,
        string $sourceDriveName,
        string $destType,
        string $destPath,
        ?string $destUser = null,
        string $syncMode = 'copy',
        string $schedule = 'manual',
    ): JSONResponse {
        $job = $this->syncJobService->createJob(
            $tenantId, $name, $sourceType, $sourceSiteId,
            $sourceDriveId, $sourceDriveName,
            $destType, $destPath, $destUser,
            $syncMode, $schedule,
        );
        return new JSONResponse($job, Http::STATUS_CREATED);
    }

    /**
     * @NoAdminRequired
     */
    public function update(int $id): JSONResponse {
        try {
            $data = $this->request->getParams();
            $job = $this->syncJobService->updateJob($id, $data);
            return new JSONResponse($job);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Job not found'], Http::STATUS_NOT_FOUND);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function delete(int $id): JSONResponse {
        try {
            $this->syncJobService->deleteJob($id);
            return new JSONResponse([], Http::STATUS_NO_CONTENT);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Job not found'], Http::STATUS_NOT_FOUND);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function start(int $id): JSONResponse {
        try {
            $job = $this->syncJobService->startJob($id);
            return new JSONResponse($job);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Job not found'], Http::STATUS_NOT_FOUND);
        } catch (\Exception $e) {
            return new JSONResponse(['error' => $e->getMessage()], Http::STATUS_INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function stop(int $id): JSONResponse {
        try {
            $job = $this->syncJobService->stopJob($id);
            return new JSONResponse($job);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Job not found'], Http::STATUS_NOT_FOUND);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function progress(int $id): JSONResponse {
        try {
            $progress = $this->syncJobService->getProgress($id);
            return new JSONResponse($progress);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Job not found'], Http::STATUS_NOT_FOUND);
        }
    }
}
