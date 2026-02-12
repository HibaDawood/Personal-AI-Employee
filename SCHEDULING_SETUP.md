# Silver Tier AI Employee - Scheduling Setup

This document explains how to set up the scheduling system for the Silver Tier AI Employee.

## Task Schedule

The scheduler runs the following tasks:

- **Every 2 minutes**: Check for new tasks in Needs_Action/
- **Every 5 minutes**: Update Dashboard.md
- **Every 30 minutes**: Health check all watchers
- **Every 6 hours**: LinkedIn check
- **Daily 8 AM**: Morning briefing summary
- **Daily 6 PM**: End of day summary
- **Weekly Sunday 8 PM**: Weekly business review

## Platform-Specific Setup

### Windows

1. Run the batch file to start the scheduler:
   ```
   run_scheduled_tasks.bat
   ```

2. To run the scheduler as a Windows service, import the XML file:
   - Open Task Scheduler
   - Select "Import Task..."
   - Choose `windows_task_scheduler.xml`
   - Update the path in the XML file to match your installation directory

### macOS/Linux

1. Make the setup script executable:
   ```
   chmod +x crontab_setup.sh
   ```

2. Run the setup script:
   ```
   ./crontab_setup.sh
   ```

For macOS specifically, you can also use the launchd plist:
1. Copy the plist file to ~/Library/LaunchAgents/
2. Load it with: `launchctl load ~/Library/LaunchAgents/macos_launchd.plist`

## Dependencies

Make sure to install the required Python packages:
```
pip install schedule psutil
```

## Health Monitoring

The scheduler includes health monitoring that:
- Checks if watcher processes are running
- Restarts crashed processes
- Creates alerts in Needs_Action/ if issues are detected
- Logs all activities to Logs/scheduler.log

## Configuration

The schedule_config.json file contains the configuration for all scheduled tasks. You can modify this file to adjust timing or commands as needed.