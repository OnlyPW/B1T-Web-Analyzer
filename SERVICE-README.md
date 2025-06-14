# B1T Web Analyzer Service Setup

Dieses Dokument beschreibt, wie Sie den B1T Web Analyzer als Systemdienst einrichten können.

## Service Installation

Um den B1T Web Analyzer als Systemdienst zu installieren, führen Sie das Installations-Skript aus:

```bash
./install-service.sh
```

Dieses Skript wird:
- Die Service-Datei nach `/etc/systemd/system/` kopieren
- Den systemd-Daemon neu laden
- Den Service aktivieren (automatischer Start beim Booten)
- Den Service starten
- Den Service-Status anzeigen

## Service-Verwaltung

Nach der Installation können Sie den Service mit folgenden Befehlen verwalten:

### Service starten
```bash
sudo systemctl start b1t-analyzer
```

### Service stoppen
```bash
sudo systemctl stop b1t-analyzer
```

### Service neu starten
```bash
sudo systemctl restart b1t-analyzer
```

### Service-Status prüfen
```bash
sudo systemctl status b1t-analyzer
```

### Automatischen Start aktivieren/deaktivieren
```bash
# Aktivieren (Start beim Booten)
sudo systemctl enable b1t-analyzer

# Deaktivieren
sudo systemctl disable b1t-analyzer
```

## Logs anzeigen

Um die Service-Logs anzuzeigen:

```bash
# Aktuelle Logs anzeigen
sudo journalctl -u b1t-analyzer

# Logs in Echtzeit verfolgen
sudo journalctl -u b1t-analyzer -f

# Nur die letzten 50 Zeilen anzeigen
sudo journalctl -u b1t-analyzer -n 50
```

## Service deinstallieren

Um den Service vollständig zu entfernen:

```bash
./uninstall-service.sh
```

## Service-Konfiguration

Die Service-Datei befindet sich unter `/etc/systemd/system/b1t-analyzer.service` und enthält folgende Konfiguration:

- **Arbeitsverzeichnis**: `/root/b1t-web-analyzer`
- **Ausführbare Datei**: `/usr/bin/python3 /root/b1t-web-analyzer/app.py`
- **Benutzer**: root
- **Automatischer Neustart**: Ja (nach 10 Sekunden bei Fehlern)
- **Logging**: systemd journal

## Zugriff auf die Webanwendung

Nach dem Start des Services ist die Webanwendung verfügbar unter:
- http://localhost:5000
- http://127.0.0.1:5000
- http://[SERVER-IP]:5000

## Troubleshooting

### Service startet nicht
1. Prüfen Sie die Logs: `sudo journalctl -u b1t-analyzer`
2. Stellen Sie sicher, dass Python3 installiert ist
3. Überprüfen Sie die Dateiberechtigungen
4. Stellen Sie sicher, dass Port 5000 verfügbar ist

### Service stoppt unerwartet
1. Prüfen Sie die Logs auf Fehlermeldungen
2. Überprüfen Sie die Systemressourcen (RAM, CPU)
3. Stellen Sie sicher, dass alle Abhängigkeiten installiert sind

### Port bereits in Verwendung
Wenn Port 5000 bereits verwendet wird, können Sie die Anwendung so konfigurieren, dass sie einen anderen Port verwendet, indem Sie die `app.py` entsprechend anpassen.