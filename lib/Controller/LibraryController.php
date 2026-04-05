<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Controller;

use OCA\Ms365Sync\AppInfo\Application;
use OCA\Ms365Sync\Service\MicrosoftGraphService;
use OCA\Ms365Sync\Service\SettingsService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class LibraryController extends Controller {
    public function __construct(
        IRequest $request,
        private SettingsService $settingsService,
        private MicrosoftGraphService $graphService,
    ) {
        parent::__construct(Application::APP_ID, $request);
    }

    private function getTokenForTenant(int $tenantId): string {
        $tenant = $this->settingsService->getTenant($tenantId);
        $secret = $this->settingsService->getDecryptedSecret($tenant);
        return $this->graphService->getToken($tenant->getTenantId(), $tenant->getClientId(), $secret);
    }

    /**
     * @NoAdminRequired
     */
    public function listMyDrives(int $tenantId, string $userId): JSONResponse {
        try {
            $token = $this->getTokenForTenant($tenantId);
            $drives = $this->graphService->listUserDrives($token, $userId);
            return new JSONResponse($drives);
        } catch (\Exception $e) {
            return new JSONResponse(['error' => $e->getMessage()], Http::STATUS_BAD_REQUEST);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function listSites(int $tenantId): JSONResponse {
        try {
            $token = $this->getTokenForTenant($tenantId);
            $sites = $this->graphService->listSites($token);
            return new JSONResponse($sites);
        } catch (\Exception $e) {
            return new JSONResponse(['error' => $e->getMessage()], Http::STATUS_BAD_REQUEST);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function listDrives(int $tenantId, string $siteId): JSONResponse {
        try {
            $token = $this->getTokenForTenant($tenantId);
            $drives = $this->graphService->listSiteDrives($token, $siteId);
            return new JSONResponse($drives);
        } catch (\Exception $e) {
            return new JSONResponse(['error' => $e->getMessage()], Http::STATUS_BAD_REQUEST);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function listUsers(int $tenantId): JSONResponse {
        try {
            $token = $this->getTokenForTenant($tenantId);
            $users = $this->graphService->listUsers($token);
            return new JSONResponse($users);
        } catch (\Exception $e) {
            return new JSONResponse(['error' => $e->getMessage()], Http::STATUS_BAD_REQUEST);
        }
    }

    /**
     * @NoAdminRequired
     */
    public function listUserDrives(int $tenantId, string $userId): JSONResponse {
        try {
            $token = $this->getTokenForTenant($tenantId);
            $drives = $this->graphService->listUserDrives($token, $userId);
            return new JSONResponse($drives);
        } catch (\Exception $e) {
            return new JSONResponse(['error' => $e->getMessage()], Http::STATUS_BAD_REQUEST);
        }
    }
}
