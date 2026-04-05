<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version001000Date20260405000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        // Azure Tenants table
        if (!$schema->hasTable('ms365sync_tenants')) {
            $table = $schema->createTable('ms365sync_tenants');
            $table->addColumn('id', Types::INTEGER, [
                'autoincrement' => true,
                'notnull' => true,
            ]);
            $table->addColumn('name', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('tenant_id', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('client_id', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('client_secret', Types::TEXT, [
                'notnull' => true,
            ]);
            $table->addColumn('status', Types::STRING, [
                'notnull' => true,
                'length' => 32,
                'default' => 'unchecked',
            ]);
            $table->addColumn('created_at', Types::DATETIME, [
                'notnull' => true,
            ]);
            $table->addColumn('updated_at', Types::DATETIME, [
                'notnull' => true,
            ]);
            $table->setPrimaryKey(['id']);
        }

        // Sync Jobs table
        if (!$schema->hasTable('ms365sync_jobs')) {
            $table = $schema->createTable('ms365sync_jobs');
            $table->addColumn('id', Types::INTEGER, [
                'autoincrement' => true,
                'notnull' => true,
            ]);
            $table->addColumn('tenant_id', Types::INTEGER, [
                'notnull' => true,
            ]);
            $table->addColumn('name', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('source_type', Types::STRING, [
                'notnull' => true,
                'length' => 32,
            ]);
            $table->addColumn('source_site_id', Types::STRING, [
                'notnull' => false,
                'length' => 512,
            ]);
            $table->addColumn('source_drive_id', Types::STRING, [
                'notnull' => true,
                'length' => 512,
            ]);
            $table->addColumn('source_drive_name', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('dest_type', Types::STRING, [
                'notnull' => true,
                'length' => 32,
            ]);
            $table->addColumn('dest_path', Types::STRING, [
                'notnull' => true,
                'length' => 1024,
            ]);
            $table->addColumn('dest_user', Types::STRING, [
                'notnull' => false,
                'length' => 255,
            ]);
            $table->addColumn('sync_mode', Types::STRING, [
                'notnull' => true,
                'length' => 32,
                'default' => 'copy',
            ]);
            $table->addColumn('schedule', Types::STRING, [
                'notnull' => true,
                'length' => 64,
                'default' => 'manual',
            ]);
            $table->addColumn('status', Types::STRING, [
                'notnull' => true,
                'length' => 32,
                'default' => 'idle',
            ]);
            $table->addColumn('last_run_at', Types::DATETIME, [
                'notnull' => false,
            ]);
            $table->addColumn('last_error', Types::TEXT, [
                'notnull' => false,
            ]);
            $table->addColumn('bytes_transferred', Types::BIGINT, [
                'notnull' => true,
                'default' => 0,
            ]);
            $table->addColumn('files_transferred', Types::INTEGER, [
                'notnull' => true,
                'default' => 0,
            ]);
            $table->addColumn('rclone_job_id', Types::INTEGER, [
                'notnull' => false,
            ]);
            $table->addColumn('nc_token_id', Types::INTEGER, [
                'notnull' => false,
            ]);
            $table->addColumn('enabled', Types::BOOLEAN, [
                'notnull' => true,
                'default' => true,
            ]);
            $table->addColumn('created_at', Types::DATETIME, [
                'notnull' => true,
            ]);
            $table->addColumn('updated_at', Types::DATETIME, [
                'notnull' => true,
            ]);
            $table->setPrimaryKey(['id']);
            $table->addIndex(['tenant_id'], 'ms365sync_jobs_tenant_idx');
            $table->addIndex(['status'], 'ms365sync_jobs_status_idx');
        }

        return $schema;
    }
}
