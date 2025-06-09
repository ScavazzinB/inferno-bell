#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Python package is installed in virtual environment
python_package_exists() {
    ./venv/bin/pip freeze | grep -i "^$1=" >/dev/null 2>&1
}

# Check for required commands
echo -e "${YELLOW}Checking required commands...${NC}"
REQUIRED_COMMANDS=("python3" "npm" "pip")
MISSING_COMMANDS=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command_exists "$cmd"; then
        MISSING_COMMANDS+=("$cmd")
    fi
done

if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    echo -e "${RED}Missing required commands: ${MISSING_COMMANDS[*]}${NC}"
    exit 1
fi

# Kill any existing processes on ports 3000 and 5000
echo -e "${YELLOW}Killing any existing processes on ports 3000 and 5000...${NC}"
kill $(lsof -t -i:3000) 2>/dev/null
kill $(lsof -t -i:5000) 2>/dev/null

# Check if npm is initialized
if [ ! -f "package.json" ]; then
    echo -e "${RED}package.json not found. Please run 'npm init' first${NC}"
    exit 1
fi

# Install or update Node.js dependencies
echo -e "${YELLOW}Installing/updating Node.js dependencies...${NC}"
npm install

# Create and setup Python virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Ensure pip and setuptools are up to date in virtual environment
echo -e "${YELLOW}Updating pip and setuptools in virtual environment...${NC}"
./venv/bin/pip install --upgrade pip setuptools

# Install Python dependencies using venv pip
echo -e "${YELLOW}Installing Python dependencies...${NC}"
./venv/bin/pip install flask flask-cors pretty_midi librosa soundfile pyfluidsynth

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo -e "${RED}Backend directory not found${NC}"
    exit 1
fi

# Start Python backend using venv python
echo -e "${GREEN}Starting Python backend...${NC}"
cd backend
../venv/bin/python3 server.py &
PYTHON_PID=$!
cd ..

# Wait for Python server to start
echo -e "${YELLOW}Waiting for Python server to initialize...${NC}"
sleep 2

# Check if server is running
if ! lsof -i:5000 > /dev/null; then
    echo -e "${RED}Failed to start Python server${NC}"
    kill $PYTHON_PID 2>/dev/null
    exit 1
fi

# Start React frontend in a new terminal
echo -e "${GREEN}Starting React frontend...${NC}"
if command_exists "gnome-terminal"; then
    gnome-terminal -- bash -c "npm start; exec bash"
elif command_exists "xterm"; then
    xterm -e "npm start; exec bash" &
elif command_exists "konsole"; then
    konsole -e bash -c "npm start; exec bash" &
else
    echo -e "${YELLOW}No suitable terminal found. Starting in current terminal...${NC}"
    npm start
fi

# Handle script termination
cleanup() {
    echo -e "${YELLOW}\nCleaning up...${NC}"
    kill $PYTHON_PID 2>/dev/null
    echo -e "${GREEN}Done!${NC}"
}

trap cleanup EXIT INT TERM

# Keep the script running
wait $PYTHON_PID