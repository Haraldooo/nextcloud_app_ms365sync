<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Db;

use JsonSerializable;
use OCP\AppFramework\Db\Entity;

/**
 * @method string getName()
 * @method void setName(string $name)
 * @method string getTenantId()
 * @method void setTenantId(string $tenantId)
 * @method string getClientId()
 * @method void setClientId(string $clientId)
 * @method string getClientSecret()
 * @method void setClientSecret(string $clientSecret)
 * @method string getStatus()
 * @method void setStatus(string $status)
 * @method \DateTime getCreatedAt()
 * @method void setCreatedAt(\DateTime $createdAt)
 * @method \DateTime getUpdatedAt()
 * @method void setUpdatedAt(\DateTime $updatedAt)
 */
class AzureTenant extends Entity implements JsonSerializable {
    protected string $name = '';
    protected string $tenantId = '';
    protected string $clientId = '';
    protected string $clientSecret = '';
    protected string $status = 'unchecked';
    protected ?\DateTime $createdAt = null;
    protected ?\DateTime $updatedAt = null;

    public function __construct() {
        $this->addType('id', 'integer');
        $this->addType('name', 'string');
        $this->addType('tenantId', 'string');
        $this->addType('clientId', 'string');
        $this->addType('clientSecret', 'string');
        $this->addType('status', 'string');
        $this->addType('createdAt', 'datetime');
        $this->addType('updatedAt', 'datetime');
    }

    public function jsonSerialize(): array {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'tenantId' => $this->tenantId,
            'clientId' => $this->clientId,
            'status' => $this->status,
            'createdAt' => $this->createdAt?->format('c'),
            'updatedAt' => $this->updatedAt?->format('c'),
            // Note: clientSecret is intentionally excluded from serialization
        ];
    }
}
