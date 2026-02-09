# Installation Guide

This guide covers all methods for installing STAC Manager on your system.

---

## Requirements

- **Python**: 3.12 or higher
- **Operating System**: Linux, macOS, or Windows
- **Package Manager**: pip or Poetry (recommended)

---

## Method 1: Install via pip (Recommended)

The simplest way to install STAC Manager for end users.

```bash
pip install stac-manager
```

**Verify installation:**

```bash
stac-manager --version
```

Expected output:

```
stac-manager, version 1.0.0
```

---

## Method 2: Install via Poetry (Recommended for Development)

Poetry provides better dependency management and virtual environment handling.

### Step 1: Install Poetry

If you don't have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Or on Windows (PowerShell):

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Step 2: Install STAC Manager

```bash
poetry add stac-manager
```

### Step 3: Activate the virtual environment

```bash
poetry shell
```

**Verify installation:**

```bash
stac-manager --version
```

---

## Method 3: Install from Source

For contributors or users who want the latest development version.

### Step 1: Clone the repository

```bash
git clone https://github.com/DecentralizedGeo/stac-manager.git
cd stac-manager
```

### Step 2: Install dependencies with Poetry

```bash
poetry install
```

This installs STAC Manager in editable mode with all development dependencies.

### Step 3: Activate the environment

```bash
poetry shell
```

**Verify installation:**

```bash
stac-manager --version
```

---

## Troubleshooting

### Python Version Issues

STAC Manager requires Python 3.12+. Check your version:

```bash
python --version
```

If you have multiple Python versions installed, you may need to use `python3.12` or `python3` explicitly:

```bash
python3.12 -m pip install stac-manager
```

### Permission Errors (Linux/macOS)

If you encounter permission errors with pip, use the `--user` flag:

```bash
pip install --user stac-manager
```

### Poetry Not Found (Windows)

After installing Poetry on Windows, you may need to add it to your PATH. Restart your terminal and try again.

---

## Next Steps

- 🚀 **[Quickstart Guide](quickstart.md)** - Run your first workflow
- 🏗️ **[System Architecture](../spec/stac-manager-v1.0.0/00-system-overview.md)** - Understand the design

---

## Updating STAC Manager

### With pip

```bash
pip install --upgrade stac-manager
```

### With Poetry

```bash
poetry update stac-manager
```

---

## Uninstalling

### With pip

```bash
pip uninstall stac-manager
```

### With Poetry

```bash
poetry remove stac-manager
```
