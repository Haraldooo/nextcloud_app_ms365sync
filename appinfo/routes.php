<?php

declare(strict_types=1);

return [
    'routes' => [
        // Page (Vue SPA shell)
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        ['name' => 'page#index', 'url' => '/{path}', 'verb' => 'GET', 'requirements' => ['path' => '.+'], 'postfix' => 'vue'],

        // Settings - Tenant CRUD
        ['name' => 'settings#listTenants', 'url' => '/api/v1/settings/tenants', 'verb' => 'GET'],
        ['name' => 'settings#createTenant', 'url' => '/api/v1/settings/tenants', 'verb' => 'POST'],
        ['name' => 'settings#updateTenant', 'url' => '/api/v1/settings/tenants/{id}', 'verb' => 'PUT'],
        ['name' => 'settings#deleteTenant', 'url' => '/api/v1/settings/tenants/{id}', 'verb' => 'DELETE'],
        ['name' => 'settings#testConnection', 'url' => '/api/v1/settings/tenants/{id}/test', 'verb' => 'POST'],
        ['name' => 'settings#getContainerConfig', 'url' => '/api/v1/settings/container', 'verb' => 'GET'],
        ['name' => 'settings#setContainerConfig', 'url' => '/api/v1/settings/container', 'verb' => 'PUT'],

        // Libraries - Browse MS365
        ['name' => 'library#listMyDrives', 'url' => '/api/v1/libraries/{tenantId}/me/drives', 'verb' => 'GET'],
        ['name' => 'library#listSites', 'url' => '/api/v1/libraries/{tenantId}/sites', 'verb' => 'GET'],
        ['name' => 'library#listDrives', 'url' => '/api/v1/libraries/{tenantId}/sites/{siteId}/drives', 'verb' => 'GET'],
        ['name' => 'library#listUsers', 'url' => '/api/v1/libraries/{tenantId}/users', 'verb' => 'GET'],
        ['name' => 'library#listUserDrives', 'url' => '/api/v1/libraries/{tenantId}/users/{userId}/drives', 'verb' => 'GET'],

        // Sync Jobs
        ['name' => 'job#list', 'url' => '/api/v1/jobs', 'verb' => 'GET'],
        ['name' => 'job#create', 'url' => '/api/v1/jobs', 'verb' => 'POST'],
        ['name' => 'job#get', 'url' => '/api/v1/jobs/{id}', 'verb' => 'GET'],
        ['name' => 'job#update', 'url' => '/api/v1/jobs/{id}', 'verb' => 'PUT'],
        ['name' => 'job#delete', 'url' => '/api/v1/jobs/{id}', 'verb' => 'DELETE'],
        ['name' => 'job#start', 'url' => '/api/v1/jobs/{id}/start', 'verb' => 'POST'],
        ['name' => 'job#stop', 'url' => '/api/v1/jobs/{id}/stop', 'verb' => 'POST'],
        ['name' => 'job#progress', 'url' => '/api/v1/jobs/{id}/progress', 'verb' => 'GET'],

        // Logs
        ['name' => 'log#getLog', 'url' => '/api/v1/logs/{jobId}', 'verb' => 'GET'],
        ['name' => 'log#tailLog', 'url' => '/api/v1/logs/{jobId}/tail', 'verb' => 'GET'],
    ],
];
