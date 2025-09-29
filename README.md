# vista_as2
This project is to answer this question: How do travel patterns differ between work-related and study-related trips? 
Hello
## Components

#### Data: 
The data is provided by the State of Victoria under Creative Commons Attribution 4.0.  

State of Victoria. (2025). Victorian Integrated Survey of Travel and Activity (VISTA). Retrieved September 11, 2025 from https://discover.data.vic.gov.au/dataset/victorian-integrated-survey-of-travel-and-activity-vista

#### Graphs and Relavant plots for analysis

Located in the `graphs` folder

#### Instruction of how to do the analysis

Located in the `instruction` folder

## Installation

### Pulling from Github

```bash
git init
git remote add origin git@github.com:phamducduy1/vista_as2.git
git pull origin main
```
**Note**: Always pull the latest version from the main branch before making any changes.
- always create a new branch for any changes you make
- make a pull request to merge your changes to the main branch by:
```bash
git checkout -b your-branch-name
# make your changes
git add .
git commit -m "Your commit message"
git push origin your-branch-name
# Go to GitHub and create a pull request
```

### Set up Pyenv

**For MacOS**
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
* Install Python build dependencies
```bash
brew install openssl readline sqlite3 xz zlib tcl-tk
```

**For Linux/Unix**
- Install dependencies:
```bash
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```
- Install Pyenv
```bash
# Automatic Installer
curl -fsSL https://pyenv.run | bash

# Setup bash environment
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc

exec "$SHELL"
```

**For Windows**
```bash
# Run PowerShell as Administrator
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

**Add to PATH (Windows)**

Open System Properties → Advanced → Environment Variables
Add these to your User PATH:
- ``%USERPROFILE%\.pyenv\pyenv-win\bin``
- ``%USERPROFILE%\.pyenv\pyenv-win\shims``

Restart your terminal

***For more installation instruction and troubleshooting guides, go to ``instruction`` for more information***

## Set up Python package
### Install Python packages from `requirements.txt` in a virtual environment

After setting up pyenv, create and activate a virtual environment using the Python version specified in `.python-version` (e.g., 3.11.10):

**For MacOS/Linux:**
```bash
pyenv install $(cat .python-version)
pyenv local $(cat .python-version)
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**For Windows:**
```powershell
pyenv install (Get-Content .python-version)
pyenv local (Get-Content .python-version)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

This ensures all dependencies from `requirements.txt` are installed in an isolated virtual environment.

### File guides
- `data`: contains the raw data files
- `src`: contains the source code for data processing and analysis
- `notebooks`: contains Jupyter notebooks for exploratory data analysis and visualization
- `graphs`: contains generated graphs and plots for analysis
- `instruction`: contains instructions for setting up the environment and running the analysis
- `README.md`: this file, providing an overview of the project and setup instructions
