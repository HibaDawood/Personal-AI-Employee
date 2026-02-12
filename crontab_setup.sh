#!/bin/bash

# Silver Tier AI Employee Scheduled Tasks Setup
# This script sets up cron jobs for the Silver Tier AI Employee

set -e  # Exit on any error

echo "Setting up Silver Tier AI Employee scheduled tasks..."

# Change to the project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Install required packages
echo "Installing required packages..."
pip3 install schedule psutil

# Create the crontab entry
CRON_ENTRY="*/2 * * * * cd $SCRIPT_DIR && /usr/bin/python3 orchestrator.py --check >> $SCRIPT_DIR/Logs/orchestrator.log 2>&1"
CRON_ENTRY_5MIN="*/5 * * * * cd $SCRIPT_DIR && /usr/bin/python3 orchestrator.py --update-dashboard >> $SCRIPT_DIR/Logs/dashboard.log 2>&1"
CRON_ENTRY_30MIN="*/30 * * * * cd $SCRIPT_DIR && /usr/bin/python3 orchestrator.py --health-check >> $SCRIPT_DIR/Logs/health.log 2>&1"
CRON_ENTRY_6HOUR="0 */6 * * * cd $SCRIPT_DIR && /usr/bin/python3 linkedin_integration.py --check >> $SCRIPT_DIR/Logs/linkedin.log 2>&1"
CRON_ENTRY_MORNING="0 8 * * * cd $SCRIPT_DIR && /usr/bin/python3 orchestrator.py --morning-brief >> $SCRIPT_DIR/Logs/morning.log 2>&1"
CRON_ENTRY_EVENING="0 18 * * * cd $SCRIPT_DIR && /usr/bin/python3 orchestrator.py --evening-summary >> $SCRIPT_DIR/Logs/evening.log 2>&1"
CRON_ENTRY_WEEKLY="0 20 * * 0 cd $SCRIPT_DIR && /usr/bin/python3 orchestrator.py --weekly-review >> $SCRIPT_DIR/Logs/weekly.log 2>&1"

# Backup existing crontab
crontab -l > mycron_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "No existing crontab to backup"

# Add our entries to the crontab
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_5MIN") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_30MIN") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_6HOUR") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_MORNING") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_EVENING") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_WEEKLY") | crontab -

echo "Cron jobs added successfully!"
echo "Current crontab:"
crontab -l

echo ""
echo "Setup complete! The following tasks are now scheduled:"
echo "- Every 2 minutes: Check for new tasks in Needs_Action/"
echo "- Every 5 minutes: Update Dashboard.md"
echo "- Every 30 minutes: Health check all watchers"
echo "- Every 6 hours: LinkedIn check"
echo "- Daily 8 AM: Morning briefing summary"
echo "- Daily 6 PM: End of day summary"
echo "- Weekly Sunday 8 PM: Weekly business review"