# Pyenv Installation Guide for Team Collaboration

This guide provides instructions for installing pyenv and Python 3.11.10 across different operating systems to ensure a consistent development environment for all team members.

## Table of Contents
- [What is Pyenv?](#what-is-pyenv)
- [Prerequisites](#prerequisites)
- [Installation Instructions](#installation-instructions)
  - [macOS](#macos)
  - [Linux/Ubuntu/Debian](#linuxubuntudebian)
  - [Windows](#windows)
- [Setting Python 3.11.10](#setting-python-31110)
- [Project Setup](#project-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## What is Pyenv?

Pyenv is a Python version management tool that allows you to easily switch between multiple versions of Python. It's perfect for collaborative projects where everyone needs to use the same Python version.

## Prerequisites

Before installing pyenv, ensure you have:
- Git installed on your system
- Basic command line knowledge
- Administrator/sudo access (for some installation steps)

## Installation Instructions

### macOS

#### Option 1: Using Homebrew (Recommended)
```bash
# Install Homebrew if you haven't already
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install pyenv
brew update
brew install pyenv

# Add pyenv to your shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# For bash users, replace ~/.zshrc with ~/.bash_profile
```

#### Option 2: Using Git
```bash
# Clone pyenv repository
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

# Add to shell configuration (for zsh)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```

#### Install Python build dependencies
```bash
brew install openssl readline sqlite3 xz zlib tcl-tk
```

### Linux/Ubuntu/Debian

#### Step 1: Install dependencies
```bash
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

#### Step 2: Install pyenv using git
```bash
# Clone pyenv repository
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

# Add to bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Restart shell
exec "$SHELL"
```

### Windows

For Windows users, we recommend using **pyenv-win**, a Windows port of pyenv.

#### Option 1: Using PowerShell (Recommended)
```powershell
# Run PowerShell as Administrator
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

#### Option 2: Using Git
```powershell
# Clone pyenv-win repository
git clone https://github.com/pyenv-win/pyenv-win.git "$HOME\.pyenv"
```

#### Add to PATH (Windows)
1. Open System Properties → Advanced → Environment Variables
2. Add these to your User PATH:
   - `%USERPROFILE%\.pyenv\pyenv-win\bin`
   - `%USERPROFILE%\.pyenv\pyenv-win\shims`
3. Restart your terminal

## Setting Python 3.11.10

Once pyenv is installed, install Python 3.11.10:

```bash
# List available Python versions (optional)
pyenv install --list | grep 3.11

# Install Python 3.11.10
pyenv install 3.11.10

# Set as global default (optional)
pyenv global 3.11.10

# Or set for current project only (recommended for project work)
pyenv local 3.11.10
```

## Project Setup

For collaborative projects, create a `.python-version` file in your project root:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Set the local Python version
pyenv local 3.11.10

# This creates a .python-version file
# Commit this file to your repository
git add .python-version
git commit -m "Add Python version specification"
```

Now when team members enter the project directory, pyenv will automatically switch to Python 3.11.10.

## Verification

Verify your installation:

```bash
# Check pyenv version
pyenv --version

# Check installed Python versions
pyenv versions

# Check current Python version
python --version
# Should output: Python 3.11.10

# Check Python path
which python
# Should show a path within .pyenv directory
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "pyenv: command not found"
- **Solution**: Restart your terminal or run `source ~/.bashrc` (or `~/.zshrc` for macOS)

#### 2. "BUILD FAILED" when installing Python
- **Solution**: Ensure all build dependencies are installed (see Prerequisites section for your OS)

#### 3. Python version not changing
- **Solution**: 
  ```bash
  # Check if pyenv is properly initialized
  pyenv init
  
  # Rehash pyenv shims
  pyenv rehash
  ```

#### 4. Windows: Scripts not executing
- **Solution**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell as Administrator

#### 5. macOS: SSL certificate issues
- **Solution**: 
  ```bash
  # Install certificates
  brew install ca-certificates
  ```

### Getting Help

- Pyenv GitHub: https://github.com/pyenv/pyenv
- Pyenv-win GitHub: https://github.com/pyenv-win/pyenv-win
- Check existing issues or create new ones on the respective repositories

## Team Collaboration Best Practices

1. **Always commit `.python-version` file** to your repository
2. **Document any additional Python packages** in `requirements.txt` or use `pipenv`/`poetry`
3. **Use virtual environments** in addition to pyenv for package isolation:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Regular updates**: Keep pyenv updated to access new Python versions
   ```bash
   # macOS with Homebrew
   brew upgrade pyenv
   
   # Others
   cd ~/.pyenv && git pull
   ```

## Notes for Cross-Platform Development

- Line ending differences: Configure Git to handle line endings appropriately
  ```bash
  git config --global core.autocrlf true  # Windows
  git config --global core.autocrlf input # macOS/Linux
  ```
- Path separators: Use `os.path.join()` or `pathlib` in Python code for cross-platform compatibility
- Be aware that some Python packages may have OS-specific dependencies

---

**Last Updated**: 2024
**Python Version**: 3.11.10
**Supported OS**: macOS, Linux, Windows