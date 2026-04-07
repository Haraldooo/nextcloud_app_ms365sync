## Spezifikationen: Nextcloud External App (AppAPI) Entwicklung

### 1. Architektur-Überblick
Die Anwendung wird nicht als klassische PHP-App im Nextcloud-Core entwickelt, sondern als **External App (ExApp)** auf Basis des Nextcloud AppAPI-Frameworks.
* **Die ExApp:** Ein eigenständiger Webserver (z. B. geschrieben in Python, Node.js, Go), der in einem isolierten Docker-Container läuft.
* **Kommunikation:** Die App kommuniziert ausschließlich über standardisierte REST/WebDAV/OCS-APIs mit dem Nextcloud-Core.
* **UI-Integration:** Das Frontend (JS/CSS) wird vom Container gehostet, aber im Kontext der Nextcloud-Web-UI im Browser des Nutzers gerendert.
* **Orchestrierung:** Der Nextcloud "Deploy Daemon" steuert den Lebenszyklus des Containers (Start, Stopp, Update) und injiziert dynamische Ports sowie Netzwerkrouten.

### 2. Vorgaben an das App-Design & Code
* **Technologie-Wahl:** Die Programmiersprache ist frei wählbar. Es wird jedoch dringend empfohlen, vorhandene offizielle oder Community-SDKs zu nutzen (z. B. `nc_py_api` für Python), da diese das API-Handshake, die Token-Verifizierung und das Routing automatisch abwickeln.
* **Zustandslosigkeit (Stateless):** Der Container muss komplett zustandslos sein. Lokale Daten auf dem Container-Dateisystem gehen bei Updates verloren. Persistente Daten müssen über die Nextcloud-API (Dateien) oder eine externe Datenbank gespeichert werden.
* **Registrierung:** Die App muss ein Manifest (meist `info.json`) an einem definierten Endpunkt ausliefern, das Berechtigungen, UI-Einstiegspunkte und Navigationselemente definiert.


### 4. Deployment & CI/CD (Das "Paket")
* **Artefakt:** Das finale Auslieferungsformat der App ist ausschließlich ein versioniertes **Docker-Image** (keine ZIP-Archive oder PHP-Ordner).
* **Registry:** Das Image muss in eine Container-Registry (z. B. GitHub Container Registry `ghcr.io` oder eine private Registry) gepusht werden.
* **Installation:** Das Deployment erfolgt via Sideloading über die Nextcloud CLI (`occ app_api:app:deploy <image_url>`). Der Code muss so geschrieben sein, dass Updates (Container stoppen, neues Image ziehen, starten) ohne manuellen Migrationsaufwand im Container funktionieren.

