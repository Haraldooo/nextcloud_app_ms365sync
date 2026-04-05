<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Db;

use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;

/**
 * @extends QBMapper<SyncJob>
 */
class SyncJobMapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'ms365sync_jobs', SyncJob::class);
    }

    /**
     * @return SyncJob[]
     */
    public function findAll(): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->orderBy('name', 'ASC');
        return $this->findEntities($qb);
    }

    public function findById(int $id): SyncJob {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id)));
        return $this->findEntity($qb);
    }

    /**
     * @return SyncJob[]
     */
    public function findByStatus(string $status): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('status', $qb->createNamedParameter($status)));
        return $this->findEntities($qb);
    }

    /**
     * @return SyncJob[]
     */
    public function findByTenantId(int $tenantId): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('tenant_id', $qb->createNamedParameter($tenantId)));
        return $this->findEntities($qb);
    }

    /**
     * @return SyncJob[]
     */
    public function findScheduledDue(): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('enabled', $qb->createNamedParameter(true, \OCP\DB\QueryBuilder\IQueryBuilder::PARAM_BOOL)))
            ->andWhere($qb->expr()->neq('schedule', $qb->createNamedParameter('manual')))
            ->andWhere($qb->expr()->neq('status', $qb->createNamedParameter('running')));
        return $this->findEntities($qb);
    }
}
