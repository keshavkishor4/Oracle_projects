#!/bin/bash
echo "export PYTHONPATH=\"/opt/faops/spe/fapodcapacity/utils/python3/el7\"" >> ~/.bashrc
echo 'export PATH="$PYTHONPATH/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="/opt/faops/spe/fapodcapacity/utils/sqllite/bin:$PATH"' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/opt/faops/spe/fapodcapacity/utils/sqllite/lib' >> ~/.bashrc
source ~/.bashrc

oci_dir=~/.oci/
if [ ! -d "$oci_dir" ]; then
    mkdir "$oci_dir"
    echo "Created directory $oci_dir"
fi
os_ver=$(cat /etc/redhat-release | awk '{print $4}')

if [[ $os_ver == "Linux" ]]; then
    var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session import --session-archive /opt/faops/spe/fapodcapacity/creds/fapod_oci_config.zip --force ;
fi

# Function to check if virtual environment exists, create it if it doesn't, and activate it
if [[ -f "db.sqlite3" ]]; then
    echo "DB File availabe, Deleting db sql file..."
    rm -f db.sqlite3
fi
create_virtualenv() {
    system=$(uname)
    if [ "$system" = "Darwin" ]; then
        if [ ! -d "../django" ]; then
            echo "Virtual environment not found. Creating virtual environment..."
            python3 -m venv ../django
        fi
        echo "Activating virtual environment..."
        source ../django/bin/activate
        echo "Upgrading pip...."
        python3 -m pip install --upgrade pip
        #oci sess auth commands
        #var_OCI_CONFIG_FILE=~/.oci/config
        #var_OCI_CLI_PROFILE=fapod_oci_config
        #var_OCI_CLI_AUTH=security_token
        #/bin/bash -c "oci session authenticate --profile-name ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --auth ${var_OCI_CLI_AUTH}; exec /bin/bash -i"
        #python3 ocisessauth.py
        #echo "Upgrading pip to the latest version..."
        # pip install --upgrade pip
        # echo "Installing packages from requirements.txt..."
        pip install  -r requirements.txt
    elif [ "$system" = "Linux" ]; then
        echo "Activating virtual environment..."
        source /opt/faops/spe/fapodcapacity/django/bin/activate
    else 
        echo "Script is running on an unknown system."
    fi
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
    python3 manage.py runserver 0.0.0.0:8000
else
    echo "Virtual environment is not activated."
fi
