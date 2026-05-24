#!/bin/sh
# AlertManager entrypoint script
# Substitutes environment variables in alertmanager.yml before starting AlertManager

set -e

# Source file
SOURCE_CONFIG="/etc/alertmanager/alertmanager.yml"
TEMP_CONFIG="/tmp/alertmanager.yml"

# Simple shell-based variable substitution
# Read the config file and replace ${VAR} with environment variable values
if [ -f "$SOURCE_CONFIG" ]; then
    # Use sed to replace ${SLACK_WEBHOOK_URL} with the actual value
    sed "s|\${SLACK_WEBHOOK_URL}|${SLACK_WEBHOOK_URL}|g" "$SOURCE_CONFIG" > "$TEMP_CONFIG"
    
    # Copy the substituted config back (using tee to avoid permission issues)
    cat "$TEMP_CONFIG" > "$SOURCE_CONFIG"
fi

# Start AlertManager with the original command arguments
exec /bin/alertmanager "$@"
