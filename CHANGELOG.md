# Changelog

## 0.2.6 — 2026-11-26

### Added

- A storage-purpose selector during setup: Backups, Media, or Shared folder (Share).
- Purpose-aware SMB/CIFS and NFS requests and a storage-purpose sensor.
- German and English labels and descriptions for all purposes.
- Tests for both protocols, all purposes, conditional forms, legacy defaults,
  credential-safe entry metadata and Supervisor request serialization.

### Improved

- The default backup destination option and sensor only appear for backup storage.
- Storage status, device descriptions and the reconnect button use general
  network-storage wording.
- Updated integration version to 0.2.6.

### Upgrade

Restart Home Assistant after updating. Existing entries and Supervisor mounts
keep their backup purpose and settings. The purpose selection is available for
new entries; existing mounts are not reconfigured automatically. Automated tests
do not connect to a live NAS or create, remove, or restore real storage mounts.
