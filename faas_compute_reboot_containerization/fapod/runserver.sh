#!/bin/bash

# Function to check if virtual environment exists, create it if it doesn't, and activate it
create_virtualenv() {
    if [ ! -d "../django" ]; then
        echo "Virtual environment not found. Creating virtual environment..."
        python3 -m venv ../django
    fi
    echo "Activating virtual environment..."
    source ../django/bin/activate
    #echo "Upgrading pip to the latest version..."
    # pip install --upgrade pip
    # echo "Installing packages from requirements.txt..."
    pip install --no-cache-dir --progress-bar=pretty -r requirements.txt
}

# Call the function
create_virtualenv

# Define a function to pull a Git repository

function pull_repo() {
  local REPO_URL="git@orahub.oci.oraclecorp.com:fsre_mw/pod_capacity_dashboard.git"
  LOCAL_DIR=$(pwd)

  # Clone or pull the repository
  if [ -d "$LOCAL_DIR" ]; then
    echo "Directory availavle pull repo....."
    cd "$LOCAL_DIR"
    git pull
  else
    git clone "$REPO_URL" "$LOCAL_DIR"
  fi
}

# Call the function with the repository URL and local directory as arguments
pull_repo 
#cd "$LOCAL_DIR/fapod"
# Activate the virtual environment
# echo "Activating virtual environment..."
# source ../django/bin/activate
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Virtual environment is activated."
    python3 manage.py makemigrations
    python3 manage.py migrate
    python3 manage.py migrate --run-syncdb
    python3 manage.py runserver
else
    echo "Virtual environment is not activated."
fi

