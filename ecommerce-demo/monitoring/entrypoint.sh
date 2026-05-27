#!/bin/bash
set -e

echo "Starting alertmanager entrypoint..."
echo "SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL}"

# Substitute environment variables in alertmanager config
echo "Substituting environment variables in alertmanager config..."
sed "s|\${SLACK_WEBHOOK_URL}|${SLACK_WEBHOOK_URL}|g" /etc/alertmanager/alertmanager.yml > /etc/alertmanager/alertmanager.yml.processed

# Verify substitution worked
echo "Checking substituted config..."
grep -i "slack_webhook_url\|api_url" /etc/alertmanager/alertmanager.yml.processed || echo "No webhook URL found in config"

# Replace original with processed
mv /etc/alertmanager/alertmanager.yml.processed /etc/alertmanager/alertmanager.yml

echo "Configuration ready, starting alertmanager..."
# Start alertmanager
exec /bin/alertmanager "$@"
