#!/usr/bin/env bash

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No color

echo -e "${GREEN}INFO${NC}: Attempting to start the AuraCityBotV2..."

# Check if the token file exists
TOKEN_FILE="base/resources/secrets/token.env"

if [ ! -f "$TOKEN_FILE" ]; then
  echo -e "${YELLOW}WARN${NC}: Token file '$TOKEN_FILE' not found. Please enter your token:"
  # shellcheck disable=SC2162
  read -p "AURACITYBOT_TOKEN: " TOKEN

  # Validate the token input
  if [[ -z "$TOKEN" ]]; then
    echo -e "${RED}ERROR${NC}: No token provided. Exiting..."
    exit 1
  fi

  # Create the token file and write the token
  echo "AURACITYBOT_TOKEN=${TOKEN}" > "$TOKEN_FILE"
  echo -e "${GREEN}INFO${NC}: Token saved to '$TOKEN_FILE'."
else
  echo -e "${GREEN}INFO${NC}: Token file '$TOKEN_FILE' found."
fi

# Check if the AuraCityBot screen session already exists
echo -e "${GREEN}INFO${NC}: Checking for existing AuraCityBotV2 screen session..."
if screen -list | grep -q "AuraCityBotV2"; then
  echo -e "${YELLOW}WARN${NC}: Screen session 'AuraCityBotV2' already exists. Exiting..."
  exit 1
fi

echo -e "${GREEN}INFO${NC}: Initializing..."

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

# Start the AuraCityBot in a separate screen session
echo -e "${GREEN}INFO${NC}: Starting the AuraCityBotV2..."
screen -S AuraCityBotV2 -dm bash -c "python main.py"
# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR${NC}: Failed to start AuraCityBotV2 screen session. Exiting..."
  exit 1
fi

echo -e "${GREEN}INFO${NC}: AuraCityBotV2 started successfully in a screen session."
