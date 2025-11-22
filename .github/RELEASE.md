# Release Process

This document describes how to create new releases using the automated CI/CD workflows.

## Automated Workflows

### CI Workflow ([ci.yml](.github/workflows/ci.yml))
**Triggers:** Push to `main` or `develop` branches, Pull Requests

**Jobs:**
1. **Lint and Format Check** (Ubuntu)
   - Run ruff linter
   - Check code formatting

2. **Test** (Ubuntu, macOS, Windows)
   - Run pytest with coverage
   - Upload coverage to Codecov

3. **Build Test** (Ubuntu, macOS, Windows)
   - Test PyInstaller builds
   - Verify executables are created

### CD Workflow ([cd.yml](.github/workflows/cd.yml))
**Triggers:** Git tags matching `v*.*.*` pattern, Manual workflow dispatch

**Jobs:**
1. **Create Release**
   - Create GitHub release with automated notes
   - Generate upload URLs for artifacts

2. **Build Windows**
   - Build executable for Windows
   - Upload to GitHub release

3. **Build macOS**
   - Build executable for macOS (Universal Binary)
   - Create .app bundle
   - Upload both binary and .app.zip to release

4. **Build Linux**
   - Build executable for Linux
   - Upload to GitHub release

### Test Builds Workflow ([test-build.yml](.github/workflows/test-build.yml))
**Triggers:** Manual dispatch, Weekly on Sunday

**Purpose:** Verify builds work across all platforms without creating a release

## Creating a Release

### Method 1: Git Tag (Recommended)

1. Update version in `pyproject.toml`:
   ```toml
   version = "1.0.0"
   ```

2. Update `CHANGELOG.md` with new version and changes

3. Commit changes:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Release v1.0.0"
   git push
   ```

4. Create and push tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

5. GitHub Actions will automatically:
   - Run all tests
   - Build executables for all platforms
   - Create GitHub release
   - Upload all binaries

### Method 2: Manual Workflow Dispatch

1. Go to **Actions** tab on GitHub
2. Select **CD - Release** workflow
3. Click **Run workflow**
4. Enter version (e.g., `v1.0.0`)
5. Click **Run workflow** button

## Release Artifacts

Each release includes:
- `TelegramDeletedMessagesManager-windows.exe` - Windows executable
- `TelegramDeletedMessagesManager-macos` - macOS universal binary
- `TelegramDeletedMessagesManager-macos.app.zip` - macOS app bundle
- `TelegramDeletedMessagesManager-linux` - Linux executable

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backwards compatible)
- **PATCH** version: Bug fixes (backwards compatible)

Examples:
- `v1.0.0` - Initial stable release
- `v1.1.0` - New features added
- `v1.1.1` - Bug fixes
- `v2.0.0` - Breaking changes

## Pre-release Testing

Before creating a release:

1. Run tests locally:
   ```bash
   make test
   ```

2. Test build locally:
   ```bash
   make build
   ./dist/TelegramDeletedMessagesManager
   ```

3. Run linter:
   ```bash
   make lint
   ```

4. Check formatting:
   ```bash
   make format
   ```

5. Or trigger **Test Builds** workflow on GitHub to test all platforms

## Troubleshooting

### Build Fails
- Check build logs in GitHub Actions
- Ensure all dependencies are in `pyproject.toml`
- Test build locally on your platform

### Tests Fail
- Fix failing tests before creating release
- All tests must pass for release to complete

### Release Already Exists
- Delete the tag: `git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0`
- Delete the release on GitHub
- Create new tag with different version

## Post-Release

After successful release:

1. Update `CHANGELOG.md` with "Unreleased" section
2. Announce release (social media, Discord, etc.)
3. Monitor GitHub issues for bug reports
4. Plan next release features
