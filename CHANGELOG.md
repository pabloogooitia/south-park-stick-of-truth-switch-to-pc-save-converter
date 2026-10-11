# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-11

### Added
- Nintendo Switch → PC (Steam) conversion of *South Park: The Stick of Truth* saves: story,
  quests, variables, inventory, NPC state, thumbnail and description.
- Input from single files, JKSV/Checkpoint backup folders and zip files.
- Automatic detection of the PC save folder (Windows, OneDrive, Steam Deck/Proton) and of a PC
  save to use as template.
- `--install` with automatic backup zip, `--clean`, `info` and `where` commands.
- Drag-and-drop support and a standalone Windows executable built on each release.
- Format documentation (`docs/FORMAT.md`), guides in English and Spanish, tests with synthetic saves.

### Known limitations
- The statistics screen is not converted (encrypted on PC; the template's values are kept).
- PC → Switch is not supported.
