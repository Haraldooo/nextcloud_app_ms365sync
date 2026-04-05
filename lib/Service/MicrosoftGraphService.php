<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Service;

use OCP\Http\Client\IClientService;
use Psr\Log\LoggerInterface;

class MicrosoftGraphService {
    private const GRAPH_BASE = 'https://graph.microsoft.com/v1.0';
    private const TOKEN_URL = 'https://login.microsoftonline.com/%s/oauth2/v2.0/token';

    /** @var array<string, array{token: string, expires: int}> */
    private array $tokenCache = [];

    public function __construct(
        private IClientService $clientService,
        private LoggerInterface $logger,
    ) {
    }

    public function getToken(string $tenantId, string $clientId, string $clientSecret): string {
        $cacheKey = $tenantId . ':' . $clientId;
        if (isset($this->tokenCache[$cacheKey]) && $this->tokenCache[$cacheKey]['expires'] > time()) {
            return $this->tokenCache[$cacheKey]['token'];
        }

        $client = $this->clientService->newClient();
        $response = $client->post(sprintf(self::TOKEN_URL, $tenantId), [
            'body' => [
                'grant_type' => 'client_credentials',
                'client_id' => $clientId,
                'client_secret' => $clientSecret,
                'scope' => 'https://graph.microsoft.com/.default',
            ],
        ]);

        $data = json_decode($response->getBody(), true);
        $this->tokenCache[$cacheKey] = [
            'token' => $data['access_token'],
            'expires' => time() + (int)$data['expires_in'] - 60,
        ];

        return $data['access_token'];
    }

    public function listSites(string $token): array {
        return $this->graphGet($token, '/sites?search=*');
    }

    public function listSiteDrives(string $token, string $siteId): array {
        return $this->graphGet($token, '/sites/' . urlencode($siteId) . '/drives');
    }

    public function listUsers(string $token): array {
        return $this->graphGet($token, '/users?$select=id,displayName,mail,userPrincipalName');
    }

    public function listUserDrives(string $token, string $userId): array {
        return $this->graphGet($token, '/users/' . urlencode($userId) . '/drives');
    }

    private function graphGet(string $token, string $path): array {
        $client = $this->clientService->newClient();
        $response = $client->get(self::GRAPH_BASE . $path, [
            'headers' => [
                'Authorization' => 'Bearer ' . $token,
                'Accept' => 'application/json',
            ],
        ]);

        $data = json_decode($response->getBody(), true);
        return $data['value'] ?? $data;
    }
}
