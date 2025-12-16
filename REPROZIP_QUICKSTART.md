# ReproZip Quick Start Guide

## For Linux Users

### 1. Install ReproZip

```bash
# Using conda/mamba (recommended)
conda install -c conda-forge reprozip reprounzip

# Or using pip
pip install reprozip reprounzip
```

### 2. Package the Project

```bash
# Option A: Use automated script
./pack_with_reprozip.sh test_basic.txt

# Option B: Manual steps
reprozip trace python3 main.py test_basic.txt
reprozip pack repcrec.rpz
```

### 3. Verify Package

```bash
reprozip show repcrec.rpz
```

## For macOS/Windows Users

### Option 1: Use Docker (Recommended)

```bash
# Build Docker image
docker build -t repcrec-pack .

# Run container interactively
docker run -it -v $(pwd):/app repcrec-pack bash

# Inside container, run packaging:
reprozip trace python3 main.py test_basic.txt
reprozip pack repcrec.rpz

# Exit container, the .rpz file will be in your local directory
```

### Option 2: Use Linux VM

1. Install Ubuntu 22.04 in VirtualBox/VMware
2. Install reprozip: `sudo apt install reprozip` or `pip install reprozip`
3. Copy project files to VM
4. Follow Linux instructions above

### Option 3: Use WSL2 (Windows only)

```bash
# In WSL2 Ubuntu
sudo apt update
sudo apt install reprozip reprounzip
./pack_with_reprozip.sh test_basic.txt
```

## Testing the Package

### Test Directory Unpack

```bash
reprounzip directory setup repcrec.rpz test_dir
reprounzip directory run test_dir python3 main.py test_basic.txt
```

### Test Docker Unpack

```bash
reprounzip dockerfile repcrec.rpz
docker build -t repcrec-test .
docker run --rm repcrec-test python3 main.py test_basic.txt
```

## What Gets Packed?

The `.rpz` file includes:
- ✅ All Python source files
- ✅ Test input files
- ✅ Python interpreter (if needed)
- ✅ System libraries
- ✅ Configuration files

## Troubleshooting

**Q: "reprozip: command not found"**
- A: Install reprozip (see installation steps above)

**Q: "Permission denied" on macOS**
- A: ReproZip requires Linux. Use Docker or a Linux VM.

**Q: Package is too large**
- A: Edit `config.yml` to exclude unnecessary files:
  ```bash
  reprozip edit config.yml
  # Remove __pycache__, .git, etc.
  ```

**Q: Missing files in package**
- A: Ensure all files are accessed during trace. Re-run trace with full test suite.

## Submission Checklist

Before submitting, ensure:
- [ ] `repcrec.rpz` file exists and is < 500MB
- [ ] Package can be unpacked successfully
- [ ] Unpacked version runs tests correctly
- [ ] Docker image builds from package
- [ ] `REPROZIP_SETUP.md` is included
- [ ] README includes reprozip instructions

## Need Help?

See `REPROZIP_SETUP.md` for detailed documentation.

