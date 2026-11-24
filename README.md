# NAS Backup Storage

Create a native Home Assistant backup location from an SMB/CIFS or NFS NAS share.

## What it does
The config flow creates a Supervisor mount with usage `backup`. Home Assistant then shows it in **Settings → System → Backups** for native manual and automatic backups. It is NAS-vendor neutral: TrueNAS, Synology, QNAP, and any compatible SMB/NFS server work.

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
