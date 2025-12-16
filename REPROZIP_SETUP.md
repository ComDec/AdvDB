# ReproZip Packaging Guide

This document explains how to package the RepCRec project using ReproZip for cross-architecture reproducibility, as required by the project specification (30/170 points).

## Overview

ReproZip captures all dependencies, files, and system calls needed to reproduce the execution environment. The packaged `.rpz` file can be unpacked and run on different architectures using virtual machines or containers.

## Prerequisites

ReproZip works best on Linux systems. If you're on macOS or Windows, use one of these options:

1. **Docker** (Recommended): Use the provided Dockerfile to run ReproZip in a Linux container
2. **Linux VM**: Use a Linux virtual machine (Ubuntu 20.04+ recommended)
3. **WSL2** (Windows): Use Windows Subsystem for Linux 2

## Installation

### Option 1: Using Conda/Mamba (Recommended)

```bash
conda install -c conda-forge reprozip reprounzip
# or
mamba install -c conda-forge reprozip reprounzip
```

### Option 2: Using pip (Linux only)

```bash
pip install reprozip reprounzip
```

### Option 3: Using Docker

See the `Dockerfile` in this repository for a containerized approach.

## Step-by-Step Packaging

### Step 1: Prepare the Environment

Ensure you're in a clean environment with Python 3.9+:

```bash
cd /path/to/AdvDB
python3 --version  # Should be 3.9 or higher
```

### Step 2: Trace the Execution

Run your tests under ReproZip trace to capture all dependencies:

```bash
# Trace a basic test
reprozip trace python3 main.py test_basic.txt

# Or trace all tests
reprozip trace ./run_all_tests.sh

# Or trace interactive mode (Ctrl+D to exit)
reprozip trace python3 main.py
```

This creates a `.reprozip-trace/` directory containing:
- `config.yml`: Configuration file listing all dependencies
- `trace.sqlite3`: Database of all system calls and file accesses

### Step 3: Review and Edit Configuration (Optional)

Edit the configuration to exclude unnecessary files:

```bash
reprozip show config.yml
reprozip edit config.yml
```

Common exclusions:
- `__pycache__/` directories
- `.git/` directory
- Temporary files
- IDE-specific files

### Step 4: Pack the Bundle

Create the portable `.rpz` file:

```bash
reprozip pack repcrec.rpz
```

This creates `repcrec.rpz` containing:
- All source code
- Python interpreter
- System libraries
- All dependencies

### Step 5: Verify the Package

Check the package contents:

```bash
reprozip show repcrec.rpz
```

## Unpacking and Running

### Option 1: Directory Unpacking (For Testing)

```bash
# Create a directory to unpack into
reprounzip directory setup repcrec.rpz run_dir

# Run the unpacked version
reprounzip directory run run_dir python3 main.py test_basic.txt
```

### Option 2: Docker Unpacking (For Distribution)

```bash
# Generate Dockerfile from the package
reprounzip dockerfile repcrec.rpz

# Build the Docker image
docker build -t repcrec:latest .

# Run in container
docker run --rm repcrec:latest python3 main.py test_basic.txt
```

### Option 3: Vagrant Unpacking (For VM Distribution)

```bash
# Generate Vagrantfile
reprounzip vagrant setup repcrec.rpz

# Start VM
vagrant up

# Run inside VM
vagrant ssh
cd /vagrant
python3 main.py test_basic.txt
```

## Complete Workflow Example

```bash
# 1. Clean start
cd /path/to/AdvDB
rm -rf .reprozip-trace repcrec.rpz

# 2. Trace execution
reprozip trace python3 main.py test_basic.txt

# 3. Review configuration
reprozip show config.yml

# 4. Pack
reprozip pack repcrec.rpz

# 5. Test unpacking
reprounzip directory setup repcrec.rpz test_run
reprounzip directory run test_run python3 main.py test_basic.txt

# 6. Generate Docker image
reprounzip dockerfile repcrec.rpz
docker build -t repcrec:latest .
docker run --rm repcrec:latest python3 main.py test_basic.txt
```

## Troubleshooting

### Issue: ReproZip not found on macOS

**Solution**: Use Docker (see `Dockerfile`) or a Linux VM. ReproZip requires Linux ptrace support.

### Issue: Package too large

**Solution**: Edit `config.yml` to exclude:
- `__pycache__/`
- `.git/`
- Test output files
- Documentation files (if not needed for execution)

### Issue: Missing dependencies

**Solution**: Ensure all files accessed during trace are included. Review `config.yml` and add missing files manually if needed.

## Files Included in Package

The `.rpz` package includes:
- ✅ All Python source files (`*.py`)
- ✅ Test input files (`test_*.txt`)
- ✅ Shell scripts (`run_all_tests.sh`)
- ✅ Python interpreter (if not system-wide)
- ✅ System libraries used during execution
- ✅ Configuration files

## Verification Checklist

Before submitting, verify:
- [ ] `.rpz` file can be unpacked successfully
- [ ] Unpacked version runs all tests correctly
- [ ] Docker image builds and runs successfully
- [ ] Package size is reasonable (< 500MB recommended)
- [ ] All test files are included
- [ ] README and documentation are included (if required)

## Submission

Include in your submission:
1. `repcrec.rpz` - The ReproZip package
2. `REPROZIP_SETUP.md` - This guide
3. `Dockerfile` (if using Docker approach)
4. Instructions for unpacking and running

## Additional Resources

- [ReproZip Documentation](https://docs.reprozip.org/)
- [ReproZip GitHub](https://github.com/VIDA-NYU/reprozip)
- [ReproZip Paper](https://reprozip.org/)

