#!/usr/bin/env bash

which gitleaks >/dev/null
if [ $? -ne 0 ]; then
    echo "Error: gitleaks not installed. Please install https://github.com/zricethezav/gitleaks"
    echo "Use 'brew install gitleaks' for Mac OS X."
    exit 1
fi


gitleaks --verbose --redact
if [ $? -ne 0 ]; then
    echo "Error: gitleaks has detected sensitive information in your changes."
    exit 1
fi
