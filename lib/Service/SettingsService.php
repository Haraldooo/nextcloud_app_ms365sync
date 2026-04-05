<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Service;

use OCA\Ms365Sync\AppInfo\Application;
use OCA\Ms365Sync\Db\AzureTenant;
use OCA\Ms365Sync\Db\AzureTenantMapper;
use OCP\AppFramework\Db\DoesNotExistException;
use OCP\IConfig;
use OCP\Security\ICrypto;

class SettingsService {
    public function __construct(
        private AzureTenantMapper $mapper,
        private IConfig $config,
        private ICrypto $crypto,
    ) {
    }

    /**
     * @return AzureTenant[]
     */
    public function listTenants(): array {
        return $this->mapper->findAll();
    }

    public function getTenant(int $id): AzureTenant {
        return $this->mapper->findById($id);
    }

    public function createTenant(string $name, string $tenantId, string $clientId, string $clientSecret): AzureTenant {
        $tenant = new AzureTenant();
        $tenant->setName($name);
        $tenant->setTenantId($tenantId);
        $tenant->setClientId($clientId);
        $tenant->setClientSecret($this->crypto->encrypt($clientSecret));
        $tenant->setStatus('unchecked');
        $now = new \DateTime();
        $tenant->setCreatedAt($now);
        $tenant->setUpdatedAt($now);
        return $this->mapper->insert($tenant);
    }

    public function updateTenant(int $id, string $name, string $tenantId, string $clientId, ?string $clientSecret): AzureTenant {
        $tenant = $this->mapper->findById($id);
        $tenant->setName($name);
        $tenant->setTenantId($tenantId);
        $tenant->setClientId($clientId);
        if ($clientSecret !== null) {
            $tenant->setClientSecret($this->crypto->encrypt($clientSecret));
            $tenant->setStatus('unchecked');
        }
        $tenant->setUpdatedAt(new \DateTime());
        return $this->mapper->update($tenant);
    }

    public function deleteTenant(int $id): void {
        $tenant = $this->mapper->findById($id);
        $this->mapper->delete($tenant);
    }

    public function getDecryptedSecret(AzureTenant $tenant): string {
        return $this->crypto->decrypt($tenant->getClientSecret());
    }

    public function getContainerUrl(): string {
        return $this->config->getAppValue(Application::APP_ID, 'container_url', 'http://localhost:8080');
    }

    public function setContainerUrl(string $url): void {
        $this->config->setAppValue(Application::APP_ID, 'container_url', $url);
    }

    public function getNextcloudUrl(): string {
        // Use overwrite.cli.url from NC config as default, fall back to app setting
        $systemUrl = $this->config->getSystemValueString('overwrite.cli.url', '');
        return $this->config->getAppValue(Application::APP_ID, 'nextcloud_url', $systemUrl);
    }

    public function setNextcloudUrl(string $url): void {
        $this->config->setAppValue(Application::APP_ID, 'nextcloud_url', $url);
    }
}
