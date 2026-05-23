#!/bin/bash
# Max Janisse - 2026

if [[ $1 == "-R" ]]; then
    echo -e "Removing existing 'venv' Python environment..."
    rm -fR venv
fi

if [ ! -d "venv" ]; then
    echo -e "Creating Python environment..."
    python3 -m venv venv > /dev/null
    echo -e "Activating Python environment..."
    source venv/bin/activate
    echo -e "Installing packages...\n"
    pip install -r ./requirements.txt > /dev/null
elif [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "Activating existing Python environment..."
    source venv/bin/activate
else
    echo -e "Python environment exists and is active, no action necessary..."
fi