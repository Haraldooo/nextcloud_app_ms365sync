<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Db;

use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;

/**
 * @extends QBMapper<AzureTenant>
 */
class AzureTenantMapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'ms365sync_tenants', AzureTenant::class);
    }

    /**
     * @return AzureTenant[]
     */
    public function findAll(): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->orderBy('name', 'ASC');
        return $this->findEntities($qb);
    }

    public function findById(int $id): AzureTenant {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id)));
        return $this->findEntity($qb);
    }
}
