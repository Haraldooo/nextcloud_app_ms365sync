<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Controller;

use OCA\Ms365Sync\AppInfo\Application;
use OCA\Ms365Sync\Service\RcloneApiService;
use OCA\Ms365Sync\Service\SyncJobService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class LogController extends Controller {
    public function __construct(
        IRequest $request,
        private SyncJobService $syncJobService,
        private RcloneApiService $rcloneApi,
    ) {
        parent::__construct(Application::APP_ID, $request);
    }

    /**
     * @NoAdminRequired
     */
    public function getLog(int $jobId): JSONResponse {
        try {
            $this->syncJobService->getJob($jobId);
            $log = $this->rcloneApi->getJobLog($jobId);
            return new JSONResponse(['log' => $log]);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Job not found'], Http::STATUS_NOT_FOUND);
        } catch (\Exception $e) {
            return new JSONResponse(['error' => $e->getMessage()], Http::STATUS_BAD_REQUEST);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function tailLog(int $jobId, int $lines = 50): JSONResponse {
        try {
            $this->syncJobService->getJob($jobId);
            $log = $this->rcloneApi->getJobLog($jobId, $lines);
            return new JSONResponse(['log' => $log]);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Job not found'], Http::STATUS_NOT_FOUND);
        } catch (\Exception $e) {
            return new JSONResponse(['error' => $e->getMessage()], Http::STATUS_BAD_REQUEST);
        }
    }
}
