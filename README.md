# Network Storage Manager

Connect SMB/CIFS or NFS network storage for backups, media, or shared files.

> [!IMPORTANT]
> **Restart Home Assistant after installing or updating this integration in HACS.** New custom integrations and their configuration flows are loaded only during Home Assistant startup. Do not try to add the integration before the restart has completed.

## What it does

The guided configuration creates a Supervisor mount for the purpose you select:

- **Backups:** a destination for native manual and automatic backups under **Settings → System → Backups**.
- **Media:** media storage mounted under `/media/<mount_name>` for the media browser and apps.
- **Shared folder (Share):** shared files mounted under `/share/<mount_name>` for apps with access to shared storage.

It is NAS-vendor neutral: TrueNAS, Synology, QNAP, and compatible SMB/NFS servers work.

The first form selects the purpose and protocol. The next form only displays fields relevant to SMB/CIFS or NFS. The default backup destination option is available only for backup storage. Its language follows the Home Assistant user interface: German for German users and English as the fallback.

When the form is submitted, the Supervisor tries to activate the mount. This checks that the selected target can be reached and mounted, but it does not create a remote folder. The configuration flow also prevents the same remote SMB/NFS target from being added through another Supervisor mount.

## Install through Home Assistant Marketplace

1. Open **Settings → Marketplace → ⋮ → Add from link**.
2. Add `https://github.com/psycixx/ha-network-storage-manager` as an **Integration**.
3. Open the repository in Marketplace and install it.
4. Restart Home Assistant, then add the integration under **Settings → Devices & services**.

For Home Assistant versions before 2026.11, add the same URL as a custom repository in HACS.

## Requirements

Home Assistant OS or Supervised is required. Create the intended share/export and grant the required access on the NAS first.

## Setup

1. Add **Network Storage Manager** under Devices & services.
2. Choose a mount name containing only letters, digits and underscores, a purpose (**Backups**, **Media**, or **Shared folder**), and SMB/CIFS or NFS.
3. For SMB, optionally paste a Windows UNC path such as `\\truenas\backups\home-assistant`. Otherwise enter the NAS address and remote share path manually. Subfolders are supported: use `backups/home-assistant`.
4. For NFS, enter the NAS address and an absolute exported path such as `/mnt/tank/backups/home-assistant`.
5. Enter SMB credentials when using SMB. For backup storage, you can optionally make it the default backup destination.
6. Confirm the status sensor is `active`. Backup storage appears on the native Backup page; media and shared storage are available at their respective mount paths.

The integration shows the selected purpose and polls mount health every five minutes. **Reconnect network storage** requests an immediate Supervisor reload; if it fails, the status sensor displays `unavailable` and includes a safe diagnostic message.

Existing entries created before 0.2.6 keep their backup purpose and mount settings.
The new purpose selection applies when creating a new entry; it does not remount
or repurpose existing storage. Duplicate remote targets are still rejected across
all purposes.

## Safety

Credentials are handed to the Supervisor mount manager; this integration stores only safe mount metadata. Removing the integration also removes its native Supervisor mount from Home Assistant. It does not delete files from the NAS. For backup destinations, test a restore before relying on the location.

## Validation

Automated tests cover all three purposes for SMB/CIFS and NFS, purpose-specific
forms, default-backup protection, legacy defaults, translations, safe metadata,
and mount cleanup after activation failure. GitHub Actions additionally validates
serialization with the real Supervisor SDK. Home Assistant services and mount
operations are mocked; these tests do not connect to a NAS or alter live mounts.
