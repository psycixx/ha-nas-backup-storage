# NAS Backup Storage

Create a native Home Assistant backup location from an SMB/CIFS or NFS NAS share.

> [!IMPORTANT]
> **Restart Home Assistant after installing or updating this integration in HACS.** New custom integrations and their configuration flows are loaded only during Home Assistant startup. Do not try to add the integration before the restart has completed.

## What it does
The config flow creates a Supervisor mount with usage `backup`. Home Assistant then shows it in **Settings → System → Backups** for native manual and automatic backups. It is NAS-vendor neutral: TrueNAS, Synology, QNAP, and any compatible SMB/NFS server work.

## Install through HACS
1. Open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/psycixx/ha-nas-backup-storage` with category **Integration**.
3. Find the repository in HACS and select **Download**.
4. **Restart Home Assistant.**
5. Add the integration under **Settings → Devices & services**.

## Requirements
Home Assistant OS or Supervised is required. Create a dedicated writable backup share and account on the NAS first.

## Setup
1. Install `custom_components/nas_backup_storage` and restart Home Assistant.
2. Add **NAS Backup Storage** under Devices & services.
3. Enter an internal mount name, protocol, NAS address, and either SMB share plus credentials or an absolute NFS export path.
4. Optionally make it the default backup location.
5. Confirm the status sensor is `active`, then select the location on the native Backup page.

The integration polls mount health every five minutes; use **Reconnect backup storage** to request an immediate Supervisor reload.

## Safety
Credentials are handed to the Supervisor mount manager; this integration stores only the mount name. Removing the integration deliberately does not remove the mount or any backups. Test a restore before relying on the location.
