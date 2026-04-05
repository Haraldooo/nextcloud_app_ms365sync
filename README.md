# MS365 Sync — Nextcloud App

Nextcloud-App zum Synchronisieren von Microsoft 365 OneDrive- und SharePoint-Dokumentenbibliotheken nach Nextcloud.

## Features

- Azure AD Tenant-Verbindung via App-Registrierung (Client Credentials)
- OneDrive und SharePoint Sites/Drives browsen
- Sync-Jobs konfigurieren mit Nextcloud-Zielordner
- Resiliente Kopierjobs via rclone (100GB+ Transfers)
- Jobs starten, pausieren, neustarten
- rclone-Logs im Browser einsehen
- Upload via Nextcloud WebDAV API (kompatibel mit S3-Backend)

## Architektur

```
Vue 3 Frontend  <--REST-->  NC PHP Backend  <--HTTP-->  Docker Container (rclone RC + Flask)
```

## Setup

### 1. Nextcloud App installieren

```bash
cd /path/to/nextcloud/apps
git clone <repo-url> ms365sync
cd ms365sync
make build
```

### 2. Docker Container starten

```bash
cd docker
docker-compose up -d
```

### 3. Azure AD App Registration

1. Azure Portal > App Registrations > New Registration
2. API Permissions hinzufugen (Application-Typ):
   - `Sites.Read.All`
   - `Files.Read.All`
   - `User.Read.All`
3. Admin Consent erteilen
4. Client Secret erstellen
5. Tenant ID, Client ID und Client Secret in den App-Settings eintragen

### 4. App konfigurieren

1. Nextcloud > MS365 Sync > Settings
2. Azure Tenant-Daten eingeben
3. Container-URL setzen (Standard: `http://localhost:8080`)
4. Verbindung testen

## Development

```bash
# Frontend
npm install
npm run dev

# PHP
composer install

# Docker
cd docker && docker-compose up --build
```

## Lizenz

AGPL-3.0-or-later
