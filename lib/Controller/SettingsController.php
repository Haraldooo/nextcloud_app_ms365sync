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

class SettingsController extends Controller {
    public function __construct(
        IRequest $request,
        private SettingsService $settingsService,
        private MicrosoftGraphService $graphService,
    ) {
        parent::__construct(Application::APP_ID, $request);
    }

    public function listTenants(): JSONResponse {
        return new JSONResponse($this->settingsService->listTenants());
    }

    public function createTenant(string $name, string $tenantId, string $clientId, string $clientSecret): JSONResponse {
        $tenant = $this->settingsService->createTenant($name, $tenantId, $clientId, $clientSecret);
        return new JSONResponse($tenant, Http::STATUS_CREATED);
    }

    public function updateTenant(int $id, string $name, string $tenantId, string $clientId, ?string $clientSecret = null): JSONResponse {
        try {
            $tenant = $this->settingsService->updateTenant($id, $name, $tenantId, $clientId, $clientSecret);
            return new JSONResponse($tenant);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Tenant not found'], Http::STATUS_NOT_FOUND);
        }
    }

    public function deleteTenant(int $id): JSONResponse {
        try {
            $this->settingsService->deleteTenant($id);
            return new JSONResponse([], Http::STATUS_NO_CONTENT);
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse(['error' => 'Tenant not found'], Http::STATUS_NOT_FOUND);
        }
    }

    public function testConnection(int $id): JSONResponse {
        try {
            $tenant = $this->settingsService->getTenant($id);
            $secret = $this->settingsService->getDecryptedSecret($tenant);
            $token = $this->graphService->getToken($tenant->getTenantId(), $tenant->getClientId(), $secret);

            // Try a simple Graph API call to validate
            $this->graphService->listSites($token);

            // Update status to valid
            $this->settingsService->updateTenant(
                $id,
                $tenant->getName(),
                $tenant->getTenantId(),
                $tenant->getClientId(),
                null
            );

            return new JSONResponse(['status' => 'valid', 'message' => 'Connection successful']);
        } catch (\Exception $e) {
            return new JSONResponse([
                'status' => 'invalid',
                'message' => 'Connection failed: ' . $e->getMessage(),
            ], Http::STATUS_BAD_REQUEST);
        }
    }

    public function getContainerConfig(): JSONResponse {
        return new JSONResponse([
            'url' => $this->settingsService->getContainerUrl(),
            'nextcloudUrl' => $this->settingsService->getNextcloudUrl(),
        ]);
    }

    public function setContainerConfig(string $url, ?string $nextcloudUrl = null): JSONResponse {
        $this->settingsService->setContainerUrl($url);
        if ($nextcloudUrl !== null) {
            $this->settingsService->setNextcloudUrl($nextcloudUrl);
        }
        return new JSONResponse([
            'url' => $url,
            'nextcloudUrl' => $this->settingsService->getNextcloudUrl(),
        ]);
    }
}
