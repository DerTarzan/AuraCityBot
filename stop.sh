#!/usr/bin/env bash

# Define color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No color

echo -e "${GREEN}INFO${NC}: Attempting to stop the AuraCityBotV2..."

# Check if the AuraCityBot screen session exists
echo -e "${GREEN}INFO${NC}: Checking for existing AuraCityBotV2 screen session..."
if ! screen -list | grep -q "AuraCityBotV2"; then
  echo -e "${RED}ERROR${NC}: No running screen session 'AuraCityBotV2' found. Exiting..."
  exit 1
fi

# Stop the AuraCityBotV2 screen session
echo -e "${GREEN}INFO${NC}: Stopping the AuraCityBotV2 screen session..."
screen -S AuraCityBotV2 -X quit
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR${NC}: Failed to stop AuraCityBotV2 screen session. Exiting..."
  exit 1
fi

echo -e "${GREEN}INFO${NC}: AuraCityBotV2 screen session stopped successfully."

# Deactivate the virtual environment if it is active
if [[ "$VIRTUAL_ENV" != "" ]]; then
  echo -e "${GREEN}INFO${NC}: Deactivating the virtual environment..."
  deactivate
  if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR${NC}: Failed to deactivate virtual environment. Exiting..."
    exit 1
  fi
  echo -e "${GREEN}INFO${NC}: Virtual environment deactivated."
else
  echo -e "${YELLOW}WARN${NC}: No virtual environment is currently active."
fi

echo -e "${GREEN}INFO${NC}: AuraCityBotV2 stopped successfully."
