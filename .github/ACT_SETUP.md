# Act Setup Guide

Test GitHub Actions workflows locally before pushing to avoid wasting time debugging on GitHub.

## Quick Start

### 1. Install Act

**macOS:**
```bash
brew install act
```

**Linux:**
```bash
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**Windows (PowerShell as Admin):**
```powershell
choco install act-cli
```

### 2. Install Docker

Act requires Docker to run workflows. Download from [docker.com](https://www.docker.com/products/docker-desktop/).

### 3. Test Installation

```bash
# Check act is installed
act --version

# Check Docker is running
docker ps

# List available workflows
act -l
```

## Common Commands

### Test CI Workflow
```bash
# Test linting and formatting
make test-ci

# Or directly with act
act push -j lint-and-format
```

### Test Specific Job
```bash
# Test just the linting
act -j lint-and-format

# Test on Ubuntu only
act -j test -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

### Full CI Run
```bash
# Run entire CI workflow
act push
```

### Dry Run
```bash
# See what would run without executing
act -n push
```

## Configuration

The project includes `.actrc` for sensible defaults:
- Uses medium Ubuntu images
- Enables verbose output
- Binds current directory

## Tips

1. **Start small:** Test individual jobs first
   ```bash
   act -j lint-and-format
   ```

2. **Use Makefile shortcuts:**
   ```bash
   make test-workflows  # List all workflows
   make test-ci         # Run CI
   ```

3. **Check logs:**
   ```bash
   act --verbose -j job-name
   ```

4. **Skip slow jobs:**
   Edit workflow temporarily to only run what you need

## Limitations

- Some GitHub-specific features won't work (hosted runners, secrets)
- Matrix builds can be slow
- Windows/macOS jobs run in Linux containers (may differ)

## When to Use

✅ **Use act for:**
- Testing workflow syntax
- Verifying job steps
- Testing build processes
- Quick iteration on workflows

❌ **Don't rely on act for:**
- Platform-specific builds (use GitHub Actions)
- Integration with GitHub APIs
- Secret-dependent workflows

## Troubleshooting

### "Cannot connect to Docker daemon"
```bash
# Start Docker Desktop
# Or on Linux:
sudo systemctl start docker
```

### "No workflows found"
```bash
# Make sure you're in project root
cd /path/to/Telegram-Deleted-Messages-Manager

# Check workflows exist
ls .github/workflows/
```

### Act is too slow
```bash
# Use smaller images
act -P ubuntu-latest=node:16-slim

# Or skip matrix builds
act -j lint-and-format  # Single job only
```

## Example Workflow

```bash
# 1. Make changes to workflow
vim .github/workflows/ci.yml

# 2. Test locally
make test-ci

# 3. If successful, commit and push
git add .github/workflows/ci.yml
git commit -m "Update CI workflow"
git push

# 4. Monitor on GitHub
# Go to Actions tab to see real run
```
