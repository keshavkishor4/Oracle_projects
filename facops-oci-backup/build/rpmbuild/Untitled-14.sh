#!/bin/bash

BASE_DIR="/opt/faops/spe/ocifabackup"
OCI_FILE_PATH="${BASE_DIR}/lib/python/common/ociSDK.py"
# Create a backup copy of the file
cp "${OCI_FILE_PATH}" "${OCI_FILEPATH}_backup"
comment_specific_string() {
    # Check if the function was called with an argument
    if [ -z "$1" ]; then
        echo "Error: Please provide the specific string to search for."
        return 1
    fi

    # Check if the file ""${OCI_FILE_PATH}"" exists
    if [ ! -f "${OCI_FILE_PATH}" ]; then
        echo "Error: The file '"${OCI_FILE_PATH}"' does not exist."
        return 1
    fi

    # Search for the specific string and comment out matching lines with '#'
    grep -n "$1" "${OCI_FILE_PATH}" | sed 's/:/# /' | while IFS="#" read -r line_num comment; do
        sed -i "${line_num}s/^/#/" "${OCI_FILE_PATH}"
        echo "Commented out line ${line_num}: $comment"
    done

    echo "File '"${OCI_FILE_PATH}"' has been updated with the commented lines."
}

comment_next_four_lines() {
    # Check if the function was called with an argument
    if [ -z "$1" ]; then
        echo "Error: Please provide the specific string to search for."
        return 1
    fi
    # Check if the file ""${OCI_FILE_PATH}"" exists
    if [ ! -f "${OCI_FILE_PATH}" ]; then
        echo "Error: The file '"${OCI_FILE_PATH}"' does not exist."
        return 1
    fi

     # Search for the specific string and comment out matching lines with '#'
    grep -n "$1" "${OCI_FILE_PATH}" | sed 's/:/# /' | while IFS="#" read -r line_num comment; do
        line_num==$((line_num + 1))
        sed -i "${line_num}s/^/#/" "${OCI_FILE_PATH}"
        echo "Commented out line ${line_num}: $comment"

        # Comment out the next four lines after the matched line
        next_line_num=$((line_num + 1))
        for ((i = 0; i < 4; i++)); do
            sed -i "${next_line_num}s/^/#/" "${OCI_FILE_PATH}"
            echo "Commented out line ${next_line_num}."
            next_line_num=$((next_line_num + 1))
        done
    done

    echo "File "${OCI_FILE_PATH}" has been updated with the commented lines."
}

comment_next_four_lines "self.retry_strategy = retry_strategy_via_constructor"
comment_specific_string "commonutils.cert_check()"