# Network Storage Manager

Create a native Home Assistant backup location from an SMB/CIFS or NFS NAS share.

> [!IMPORTANT]
> **Restart Home Assistant after installing or updating this integration in HACS.** New custom integrations and their configuration flows are loaded only during Home Assistant startup. Do not try to add the integration before the restart has completed.

## What it does

The guided configuration creates a Supervisor mount with usage `backup`. Home Assistant then shows it in **Settings → System → Backups** for native manual and automatic backups. It is NAS-vendor neutral: TrueNAS, Synology, QNAP, and any compatible SMB/NFS server work.

The first form selects the protocol. The next form only displays fields relevant to SMB/CIFS or NFS. Its language follows the Home Assistant user interface: German for German users and English as the fallback.

When the form is submitted, the Supervisor tries to activate the mount. This checks that the selected target can be reached and mounted, but it does not create a remote folder. The configuration flow also prevents the same remote SMB/NFS target from being added through another Supervisor mount.

## Install through Home Assistant Marketplace

1. Open **Settings → Marketplace → ⋮ → Add from link**.
2. Add `https://github.com/psycixx/ha-network-storage-manager` as an **Integration**.
3. Open the repository in Marketplace and install it.
4. Restart Home Assistant, then add the integration under **Settings → Devices & services**.

For Home Assistant versions before 2026.11, add the same URL as a custom repository in HACS.

## Requirements

Home Assistant OS or Supervised is required. Create a dedicated writable backup share and account on the NAS first.

## Setup

1. Add **Network Storage Manager** under Devices & services.
2. Choose a mount name containing only letters, digits and underscores, then choose SMB/CIFS or NFS.
3. For SMB, optionally paste a Windows UNC path such as `\\truenas\backups\home-assistant`. Otherwise enter the NAS address and remote share path manually. Subfolders are supported: use `backups/home-assistant`.
4. For NFS, enter the NAS address and an absolute exported path such as `/mnt/tank/backups/home-assistant`.
5. Enter SMB credentials when using SMB, then optionally set the location as the default backup target.
6. Confirm the status sensor is `active`, then select the location on the native Backup page.

The integration polls mount health every five minutes. **Reconnect backup storage** requests an immediate Supervisor reload; if it fails, the status sensor displays `unavailable` and includes a safe diagnostic message.

## Safety

Credentials are handed to the Supervisor mount manager; this integration stores only safe mount metadata. Removing the integration also removes its native Supervisor backup location from Home Assistant. It does not delete backup files from the NAS. Test a restore before relying on the location.
