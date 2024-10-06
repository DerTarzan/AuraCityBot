#!/usr/bin/env bash

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No color

echo -e "${GREEN}INFO${NC}: Attempting to restart the AuraCityBotV2..."

# Check if the AuraCityBot screen session exists
echo -e "${GREEN}INFO${NC}: Checking for existing AuraCityBotV2 screen session..."
if screen -list | grep -q "AuraCityBotV2"; then
  echo -e "${GREEN}INFO${NC}: Stopping the AuraCityBotV2 screen session..."
  screen -S AuraCityBotV2 -X quit
  # shellcheck disable=SC2181
  if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR${NC}: Failed to stop AuraCityBotV2 screen session. Exiting..."
    exit 1
  fi
  echo -e "${GREEN}INFO${NC}: AuraCityBotV2 screen session stopped successfully."
else
  echo -e "${YELLOW}WARN${NC}: No running screen session 'AuraCityBotV2' found."
fi

# Initialize and start the AuraCityBotV2
echo -e "${GREEN}INFO${NC}: Initializing and starting the AuraCityBotV2..."

# Check if the virtual environment exists, if not, create it
if [ ! -d "venv" ]; then
  echo -e "${YELLOW}WARN${NC}: Virtual environment not found. Creating a new one..."
  python3 -m venv venv
  # shellcheck disable=SC2181
  if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR${NC}: Failed to create virtual environment. Exiting..."
    exit 1
  fi
  echo -e "${GREEN}INFO${NC}: Virtual environment created."
fi

# Wait for venv directory to be created if necessary
while [ ! -d "venv" ]; do
  echo -e "${YELLOW}WARN${NC}: Waiting for virtual environment to be created..."
  sleep 1
done

# Activate the virtual environment
echo -e "${GREEN}INFO${NC}: Activating virtual environment..."
source venv/bin/activate
# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR${NC}: Failed to activate virtual environment. Exiting..."
  exit 1
fi

# Check and install the required pip packages
echo -e "${GREEN}INFO${NC}: Checking and installing required pip packages..."
pip install -r requirements.txt
# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR${NC}: Failed to install pip packages. Exiting..."
  exit 1
fi

# Start the AuraCityBot in a separate screen session and capture the session ID
echo -e "${GREEN}INFO${NC}: Starting the AuraCityBotV2..."
screen -S AuraCityBotV2 -dm bash -c "python main.py"
# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR${NC}: Failed to start AuraCityBotV2 screen session. Exiting..."
  exit 1
fi

# Get the screen session ID
SESSION_ID=$(screen -ls | grep AuraCityBotV2 | awk '{print $1}')

# Output success message with the session ID
echo -e "${GREEN}INFO${NC}: AuraCityBotV2 bot started successfully in screen session ID: ${GREEN}${SESSION_ID}${NC}."
