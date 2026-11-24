# Network Storage Manager

Create a native Home Assistant backup location from an SMB/CIFS or NFS NAS share.

> [!IMPORTANT]
> **Restart Home Assistant after installing or updating this integration in HACS.** New custom integrations and their configuration flows are loaded only during Home Assistant startup. Do not try to add the integration before the restart has completed.

## What it does

The config flow creates a Supervisor mount with usage `backup`. Home Assistant then shows it in **Settings → System → Backups** for native manual and automatic backups. It is NAS-vendor neutral: TrueNAS, Synology, QNAP, and any compatible SMB/NFS server work.

When the form is submitted, the Supervisor tries to activate the mount. This verifies that the target exists and can be reached with the supplied access details. If it cannot be activated, no storage configuration is created.

## Install through HACS

1. Open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/psycixx/ha-network-storage-manager` with category **Integration**.
3. Find the repository in HACS and select **Download**.
4. **Restart Home Assistant.**
5. Add the integration under **Settings → Devices & services**.

## Requirements

Home Assistant OS or Supervised is required. Create a dedicated writable backup share and account on the NAS first.

## Setup

1. Install `custom_components/network_storage_manager` and restart Home Assistant.
2. Add **Network Storage Manager** under Devices & services.
3. Enter an internal mount name and select SMB/CIFS or NFS.
4. For SMB, either paste a Windows UNC path such as `\\truenas\backups\home-assistant` or enter the NAS address and remote share path manually. Subfolders are supported: use `backups/home-assistant` as the remote share path.
5. For NFS, enter the NAS address and an absolute exported path such as `/mnt/tank/backups/home-assistant`.
6. Enter SMB credentials when using SMB, then optionally set the location as the default backup target.
7. Confirm the status sensor is `active`, then select the location on the native Backup page.

The integration polls mount health every five minutes; use **Reconnect backup storage** to request an immediate Supervisor reload.

## Safety

Credentials are handed to the Supervisor mount manager; this integration stores only safe mount metadata. Removing the integration also removes its native Supervisor backup location from Home Assistant. It does not delete backup files from the NAS. Test a restore before relying on the location.
