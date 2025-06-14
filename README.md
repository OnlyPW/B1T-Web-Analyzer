# B1T Web Analyzer

Eine webbasierte Anwendung zur Analyse von Bitcoin-Transaktionen mit RPC-Verbindung.

## Features

- **Web-Interface**: Benutzerfreundliche Oberfläche zur Konfiguration und Ausführung von Blockchain-Analysen
- **RPC-Verbindung**: Direkte Verbindung zum Bitcoin-Node über RPC
- **Job-Management**: Erstellen, überwachen und verwalten von Analyse-Jobs
- **Echtzeit-Status**: Live-Updates des Analyse-Fortschritts
- **Konfiguration**: Web-basierte RPC-Konfiguration
- **Responsive Design**: Funktioniert auf Desktop und mobilen Geräten

## Installation

1. **Abhängigkeiten installieren:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Umgebungsvariablen konfigurieren:**
   Bearbeiten Sie die `.env` Datei:
   ```
   RPC_HOST=localhost
   RPC_PORT=8332
   RPC_USER=your_username
   RPC_PASSWORD=your_password
   RPC_TIMEOUT=30
   ```

3. **B1T-Node konfigurieren:**
   Stellen Sie sicher, dass Ihr `bit.conf` folgende Einstellungen enthält:
   ```
   server=1
   rpcuser=your_username
   rpcpassword=your_password
   rpcallowip=127.0.0.1
   rpcport=8332
   ```

## Verwendung

1. **Webanwendung starten:**
   ```bash
   python3 app.py
   ```

2. **Browser öffnen:**
   Navigieren Sie zu `http://localhost:5000`

3. **RPC-Verbindung testen:**
   - Gehen Sie zu "Konfiguration"
   - Testen Sie die RPC-Verbindung
   - Speichern Sie die Einstellungen

4. **Analyse starten:**
   - Klicken Sie auf "Neue Analyse"
   - Geben Sie die gewünschten Parameter ein
   - Starten Sie die Analyse

## Analyse-Parameter

- **Job-Name**: Eindeutiger Name für die Analyse
- **Start-Block**: Erster Block der Analyse
- **End-Block**: Letzter Block der Analyse
- **Batch-Größe**: Anzahl der Blöcke pro Batch (1-10000)
- **Mindest-Nullen**: Mindestanzahl führender Nullen in Transaction-IDs
- **Alle Nullen anzeigen**: Zeigt alle Transaktionen mit führenden Nullen

## Funktionen

### Dashboard
- Übersicht über den aktuellen Status
- Fortschrittsanzeige für laufende Analysen
- Schnellzugriff auf wichtige Funktionen
- Liste der letzten Analyse-Jobs

### Job-Management
- Erstellen neuer Analyse-Jobs
- Überwachen des Fortschritts
- Anzeigen von Ergebnissen
- Herunterladen von Analyse-Daten

### Konfiguration
- RPC-Verbindungseinstellungen
- Verbindungstest
- Systeminformationen
- Hilfe und Dokumentation

## API-Endpunkte

- `GET /api/status` - Aktueller Analyse-Status
- `POST /api/start_job` - Neue Analyse starten
- `GET /api/job/<id>` - Job-Details abrufen
- `POST /api/test_connection` - RPC-Verbindung testen

## Technische Details

### Architektur
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Backend**: Flask (Python)
- **RPC-Client**: Requests-Library
- **Konfiguration**: Python-dotenv

### Sicherheit
- RPC-Credentials werden in `.env` gespeichert
- Keine Hardcoded-Passwörter
- Input-Validierung für alle Parameter

### Performance
- Asynchrone Job-Ausführung
- Batch-Verarbeitung für große Block-Bereiche
- Echtzeit-Status-Updates
- Optimierte RPC-Aufrufe

## Fehlerbehebung

### Häufige Probleme

1. **RPC-Verbindung fehlgeschlagen:**
   - Überprüfen Sie die Bitcoin-Node-Konfiguration
   - Stellen Sie sicher, dass der Node läuft
   - Überprüfen Sie Benutzername und Passwort

2. **Analyse startet nicht:**
   - Überprüfen Sie die Block-Parameter
   - Stellen Sie sicher, dass der End-Block größer als der Start-Block ist
   - Überprüfen Sie die RPC-Verbindung

3. **Langsame Performance:**
   - Reduzieren Sie die Batch-Größe
   - Überprüfen Sie die Node-Performance
   - Stellen Sie sicher, dass der Node vollständig synchronisiert ist

### Logs
Die Anwendung protokolliert wichtige Ereignisse in der Konsole. Starten Sie die Anwendung mit:
```bash
python3 app.py
```

## Entwicklung

### Projektstruktur
```
b1t-web-analyzer/
├── app.py                 # Haupt-Flask-Anwendung
├── final_analyzer_rpc.py  # RPC-Analyse-Script
├── .env                   # Umgebungsvariablen
├── requirements.txt       # Python-Abhängigkeiten
├── README.md             # Diese Datei
├── templates/            # HTML-Templates
│   ├── base.html
│   ├── index.html
│   ├── new_job.html
│   ├── job_detail.html
│   ├── jobs_list.html
│   └── config.html
└── static/              # Statische Dateien
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

### Erweiterungen
Die Anwendung kann erweitert werden um:
- Datenbank-Integration für persistente Job-Speicherung
- Benutzer-Authentifizierung
- Erweiterte Analyse-Optionen
- Export-Funktionen (CSV, JSON)
- Grafische Darstellung der Ergebnisse

## Lizenz

Dieses Projekt ist für den persönlichen und kommerziellen Gebrauch frei verfügbar.

## Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue oder kontaktieren Sie den Entwickler.
