# GitHub Actions Workflows

This directory contains CI/CD workflows for automated testing, building, and releasing.

## Workflows

### ci.yml - Continuous Integration
Runs on every push and pull request:
- Linting and formatting checks
- Tests on Ubuntu, macOS, Windows
- Build verification on all platforms

### cd.yml - Continuous Deployment
Runs on version tags (`v*.*.*`):
- Creates GitHub releases
- Builds executables for Windows, macOS, Linux
- Uploads binaries to release

### test-build.yml - Weekly Build Tests
Runs weekly and on manual trigger:
- Verifies builds work across platforms
- Uploads build artifacts

## Testing Workflows Locally

### Using Act (Recommended)

[Act](https://github.com/nektos/act) runs GitHub Actions locally using Docker.

**Install:**
```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows (with Chocolatey)
choco install act-cli
```

**Test workflows:**
```bash
# List all workflows and jobs
act -l

# Run CI workflow (push event)
act push

# Run specific job
act -j lint-and-format

# Run pull request workflow
act pull_request

# Dry run (don't actually execute)
act -n

# Run with specific event
act push -e .github/workflows/test-event.json
```

**Common act commands:**
```bash
# Test linting only
act -j lint-and-format

# Test on specific platform
act -j test -P ubuntu-latest=catthehacker/ubuntu:act-latest

# Run full CI
act push

# Test build without running tests
act -j build-test
```

### Using Local Scripts

**Run tests locally:**
```bash
make test           # Run all tests
make test-coverage  # Run with coverage
make lint           # Run linter
make format         # Format code
```

**Test build:**
```bash
make build          # Build executable
```

## Workflow Configuration

The `.actrc` file in the project root configures act with sensible defaults:
- Uses medium Ubuntu images for faster execution
- Binds current directory
- Enables verbose output

## Debugging Workflows

### View workflow logs
```bash
# On GitHub
# Go to Actions tab → Select workflow run → View logs

# Locally with act
act -j job-name --verbose
```

### Common Issues

**1. Act can't find Docker**
```bash
# Make sure Docker is running
docker ps

# Use specific Docker socket
act --container-daemon-socket /var/run/docker.sock
```

**2. Permission errors**
```bash
# Run with sudo (Linux)
sudo act

# Or add user to docker group
sudo usermod -aG docker $USER
```

**3. Slow builds**
```bash
# Use smaller images
act -P ubuntu-latest=node:16-slim

# Cache dependencies (add to workflow)
uses: actions/cache@v3
```

**4. Workflow doesn't trigger**
```bash
# Check event type
act -l  # List available jobs

# Specify event explicitly
act push  # For push events
act pull_request  # For PRs
```

## CI/CD Best Practices

1. **Test locally first** - Use act before pushing
2. **Keep workflows fast** - Use caching, parallel jobs
3. **Fail fast** - Set `fail-fast: true` in matrix
4. **Use semantic versioning** - Tag releases as `v1.2.3`
5. **Review workflow logs** - Check for warnings and errors

## Troubleshooting

### Workflow fails on GitHub but passes locally
- Check GitHub Actions runner logs
- Ensure all secrets are configured
- Verify GitHub-hosted runner environment

### Act fails but workflow passes on GitHub
- Update act to latest version: `brew upgrade act`
- Use official GitHub Docker images: `-P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest`
- Check act version compatibility

### Build size too large
- Review dependencies
- Remove unused packages
- Use `--onefile` in PyInstaller
- Strip debug symbols (platform-specific)

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Act GitHub Repository](https://github.com/nektos/act)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [PyInstaller Documentation](https://pyinstaller.org/)
