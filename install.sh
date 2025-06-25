#!/bin/bash
echo "Setting up Memex Relay API..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv memex_relay_env

# Activate virtual environment
echo "Activating virtual environment..."
source memex_relay_env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the API:"
echo "1. source memex_relay_env/bin/activate"
echo "2. python main.py"
echo ""
echo "To test the API:"
echo "python test_api.py"