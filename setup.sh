echo "Setting up your machine for DEVWKS-1016"

# echo "Installing Python3..."
# sudo apt-get update
# sudo apt-get install python3-pip

echo "Setting up virtual environment..."
sudo apt-get install python3-venv
python3 -m venv DEVWKS

echo "Installing required libraries..."
source DEVWKS/bin/activate
python3 -m pip install -r requirements.txt
deactivate

echo "Setup Completed.. Please run `source DEVWKS/bin/activate` to enter your virtual environment..."
