# Changelog

All notable changes to this project will be documented in this file.

## [1.1.1] - 2024-02-20
### Fixed
- Fixed JS syntax error when metadata (title, collection, tag) contains single quotes (e.g. `O'Reilly`).

## [1.1.0] - 2024-02-20
### Added
- Added Configuration GUI (via `config.py`) to manage API and tag preferences.
- Added support for multiple book formats (`PDF`, `EPUB`, `AZW3`, `MOBI`).
- Separated JS execution code into a dedicated template (`zotero_script.js`).

### Changed
- Improved error handling to continue processing subsequent books if one fails.
- Re-architected data parsing using JSON parsing avoiding JS syntax errors.

## [1.0.1] - 2024-02-20

- Initial creation of the plugin.
