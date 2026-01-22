#!/bin/bash
# Whisk Automation - One-Command Setup for Linux/macOS
# Run: bash setup.sh

set -e

echo -e "\033[1;36m=== Whisk Automation Setup ===\033[0m"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31mError: Python 3 not found. Please install Python 3.9 or later.\033[0m"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "Found Python $PYTHON_VERSION"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    OS="Unknown"
fi
echo -e "Detected OS: $OS"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "\033[1;33mCreating virtual environment...\033[0m"
    python3 -m venv venv
else
    echo -e "\033[1;33mVirtual environment already exists.\033[0m"
fi

# Activate venv and install dependencies
echo -e "\033[1;33mInstalling dependencies...\033[0m"
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt

# Create necessary directories
echo -e "\033[1;33mCreating project structure...\033[0m"
mkdir -p data/environments
mkdir -p data/characters
mkdir -p output
mkdir -p logs

# Create .gitkeep files
touch data/environments/.gitkeep
touch data/characters/.gitkeep

# Create default config if not exists
if [ ! -f "config.json" ]; then
    echo -e "\033[1;33mCreating default config.json...\033[0m"
    cat > config.json << 'EOF'
{
  "whisk_url": "https://labs.google/fx/tools/whisk/project",
  "browser": {
    "headless": false,
    "slow_mo": 100,
    "user_data_dir": null
  },
  "paths": {
    "environments": "./data/environments",
    "characters": "./data/characters",
    "output": "./output",
    "scenes_file": "./data/scenes.csv"
  },
  "generation": {
    "images_per_prompt": 4,
    "batches_per_scene": 2,
    "image_format": "landscape",
    "download_timeout": 60
  },
  "queue": {
    "retry_on_failure": true,
    "max_retries": 3,
    "delay_between_scenes": 5
  }
}
EOF
fi

# Install Playwright browsers
echo -e "\033[1;33mInstalling Playwright browsers...\033[0m"
playwright install chromium

echo ""
echo -e "\033[1;32m=== Setup Complete! ===\033[0m"
echo ""
echo -e "\033[1mNext steps:\033[0m"
echo "  1. Activate the virtual environment:"
echo -e "     \033[36msource venv/bin/activate\033[0m"
echo ""
echo "  2. Test the connection:"
echo -e "     \033[36mpython run.py test\033[0m"
echo ""
echo "  3. See all commands:"
echo -e "     \033[36mpython run.py --help\033[0m"
echo ""
