<?php

declare(strict_types=1);

namespace OCA\Ms365Sync\Db;

use JsonSerializable;
use OCP\AppFramework\Db\Entity;

/**
 * @method string getName()
 * @method void setName(string $name)
 * @method int getTenantId()
 * @method void setTenantId(int $tenantId)
 * @method string getSourceType()
 * @method void setSourceType(string $sourceType)
 * @method ?string getSourceSiteId()
 * @method void setSourceSiteId(?string $sourceSiteId)
 * @method string getSourceDriveId()
 * @method void setSourceDriveId(string $sourceDriveId)
 * @method string getSourceDriveName()
 * @method void setSourceDriveName(string $sourceDriveName)
 * @method string getDestType()
 * @method void setDestType(string $destType)
 * @method string getDestPath()
 * @method void setDestPath(string $destPath)
 * @method ?string getDestUser()
 * @method void setDestUser(?string $destUser)
 * @method string getSyncMode()
 * @method void setSyncMode(string $syncMode)
 * @method string getSchedule()
 * @method void setSchedule(string $schedule)
 * @method string getStatus()
 * @method void setStatus(string $status)
 * @method ?\DateTime getLastRunAt()
 * @method void setLastRunAt(?\DateTime $lastRunAt)
 * @method ?string getLastError()
 * @method void setLastError(?string $lastError)
 * @method int getBytesTransferred()
 * @method void setBytesTransferred(int $bytesTransferred)
 * @method int getFilesTransferred()
 * @method void setFilesTransferred(int $filesTransferred)
 * @method ?int getRcloneJobId()
 * @method void setRcloneJobId(?int $rcloneJobId)
 * @method ?int getNcTokenId()
 * @method void setNcTokenId(?int $ncTokenId)
 * @method bool getEnabled()
 * @method void setEnabled(bool $enabled)
 * @method \DateTime getCreatedAt()
 * @method void setCreatedAt(\DateTime $createdAt)
 * @method \DateTime getUpdatedAt()
 * @method void setUpdatedAt(\DateTime $updatedAt)
 */
class SyncJob extends Entity implements JsonSerializable {
    protected int $tenantId = 0;
    protected string $name = '';
    protected string $sourceType = '';
    protected ?string $sourceSiteId = null;
    protected string $sourceDriveId = '';
    protected string $sourceDriveName = '';
    protected string $destType = '';
    protected string $destPath = '';
    protected ?string $destUser = null;
    protected string $syncMode = 'copy';
    protected string $schedule = 'manual';
    protected string $status = 'idle';
    protected ?\DateTime $lastRunAt = null;
    protected ?string $lastError = null;
    protected int $bytesTransferred = 0;
    protected int $filesTransferred = 0;
    protected ?int $rcloneJobId = null;
    protected ?int $ncTokenId = null;
    protected bool $enabled = true;
    protected ?\DateTime $createdAt = null;
    protected ?\DateTime $updatedAt = null;

    public function __construct() {
        $this->addType('id', 'integer');
        $this->addType('tenantId', 'integer');
        $this->addType('name', 'string');
        $this->addType('sourceType', 'string');
        $this->addType('sourceSiteId', 'string');
        $this->addType('sourceDriveId', 'string');
        $this->addType('sourceDriveName', 'string');
        $this->addType('destType', 'string');
        $this->addType('destPath', 'string');
        $this->addType('destUser', 'string');
        $this->addType('syncMode', 'string');
        $this->addType('schedule', 'string');
        $this->addType('status', 'string');
        $this->addType('lastRunAt', 'datetime');
        $this->addType('lastError', 'string');
        $this->addType('bytesTransferred', 'integer');
        $this->addType('filesTransferred', 'integer');
        $this->addType('rcloneJobId', 'integer');
        $this->addType('ncTokenId', 'integer');
        $this->addType('enabled', 'boolean');
        $this->addType('createdAt', 'datetime');
        $this->addType('updatedAt', 'datetime');
    }

    public function jsonSerialize(): array {
        return [
            'id' => $this->id,
            'tenantId' => $this->tenantId,
            'name' => $this->name,
            'sourceType' => $this->sourceType,
            'sourceSiteId' => $this->sourceSiteId,
            'sourceDriveId' => $this->sourceDriveId,
            'sourceDriveName' => $this->sourceDriveName,
            'destType' => $this->destType,
            'destPath' => $this->destPath,
            'destUser' => $this->destUser,
            'syncMode' => $this->syncMode,
            'schedule' => $this->schedule,
            'status' => $this->status,
            'lastRunAt' => $this->lastRunAt?->format('c'),
            'lastError' => $this->lastError,
            'bytesTransferred' => $this->bytesTransferred,
            'filesTransferred' => $this->filesTransferred,
            'rcloneJobId' => $this->rcloneJobId,
            'enabled' => $this->enabled,
            'createdAt' => $this->createdAt?->format('c'),
            'updatedAt' => $this->updatedAt?->format('c'),
        ];
    }
}
