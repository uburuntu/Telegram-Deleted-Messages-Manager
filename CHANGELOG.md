# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows for automated testing and releases
- Comprehensive test coverage with pytest
- Ruff linting and formatting
- Cross-platform builds (Windows, macOS, Linux)

### Changed
- Migrated to Pydantic V2 ConfigDict
- Consolidated datetime imports
- Improved code organization and cleanup

### Removed
- Unused code and deprecated features
- Placeholder configuration values

## [0.1.0] - 2025-01-22

### Added
- Initial release
- Export deleted messages from Telegram chats
- Re-send exported messages to different chats
- Configurable message headers (sender name, username, date, reply links)
- Timezone adjustment for message timestamps
- Smart message batching for consecutive short messages
- FloodWait error handling for rate limiting
- Export directory auto-detection and statistics
- Flet-based cross-platform UI
- Support for standalone builds (PyInstaller, macOS .app)
- Path handling fixes for media files
- Granular header customization
- Hidden HTML reply links
- Working stop button with cancellation support

### Technical
- Telethon for Telegram API integration
- Flet for modern UI framework
- Pydantic for data validation
- Async/await throughout
- Comprehensive unit tests
- Modern Python 3.14+ support

[Unreleased]: https://github.com/uburuntu/Telegram-Deleted-Messages-Manager/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/uburuntu/Telegram-Deleted-Messages-Manager/releases/tag/v0.1.0
