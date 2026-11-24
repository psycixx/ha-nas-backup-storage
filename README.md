# NAS Backup Storage

Eine Home-Assistant-Custom-Integration, die NAS-Freigaben als native Backup-Speicherorte einrichtet.

## Ziel

Der Assistent fragt nur die Angaben ab, die für eine SMB/CIFS- oder NFS-Freigabe nötig sind. Danach erstellt er einen Supervisor-Mount mit der Nutzung **Backup**. Home Assistant zeigt ihn anschließend in **Einstellungen → System → Backups** als normalen Speicherort an.

Die Integration funktioniert mit TrueNAS, Synology, QNAP und jedem NAS mit SMB/CIFS oder NFS. Eine vorhandene Herstellerintegration ist nicht erforderlich.

## Installation

1. Den Ordner `custom_components/nas_backup_storage` nach `<config>/custom_components/` kopieren.
2. Home Assistant neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → NAS Backup Storage**.
4. Pro Freigabe Protokoll, NAS-Adresse, Freigabe bzw. NFS-Pfad und bei SMB Zugangsdaten eingeben.
5. Danach den Speicherort unter **Einstellungen → System → Backups** für manuelle oder automatische Backups auswählen.

## Sicherheit und Grenzen

- Die Freigabe-Zugangsdaten werden ausschließlich beim Supervisor-Mount hinterlegt. Der Config-Entry dieser Integration speichert nur den Namen des Mounts.
- Das Entfernen der Integration löscht den Supervisor-Mount nicht. So bleiben bereits vorhandene Backups erreichbar und der Speicher kann weiterhin von Home Assistant verwendet werden.
- Unterstützt werden Home Assistant OS und Supervised mit verfügbarem Supervisor; Home Assistant Container und Core haben keinen Supervisor-Mount-Manager.
- Der MVP erstellt keinen Benutzer und keine Freigabe auf dem NAS. Dafür werden absichtlich keine weitreichenden NAS-API-Rechte verlangt.

## Testen

Vor der produktiven Nutzung: einen manuellen verschlüsselten Backup-Lauf auf dem neuen Speicher ausführen, ihn in der Backup-Übersicht sehen und einen Wiederherstellungstest auf einer separaten HA-Instanz durchführen.
