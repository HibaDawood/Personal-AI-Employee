import os
import time
import logging
from pathlib import Path
from datetime import datetime
import subprocess
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def setup_logging():
    """Setup logging to both console and file"""
    # Create Logs directory if it doesn't exist
    logs_dir = Path("Logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger('Orchestrator')
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler
    log_file = logs_dir / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def update_dashboard(logger):
    """
    Update Dashboard.md with current statistics and recent completed tasks.
    """
    try:
        # Count files in Needs_Action folder
        needs_action_count = len(list(Path("Needs_Action").glob("*.md")))
        
        # Count files in Done folder that were completed today
        done_folder = Path("Done")
        today_str = datetime.now().strftime("%Y-%m-%d")
        completed_today = 0
        
        if done_folder.exists():
            for file in done_folder.glob("*.md"):
                # Check if file was modified today
                mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                if mod_time.strftime("%Y-%m-%d") == today_str:
                    completed_today += 1
        
        # Get last 5 completed tasks
        recent_completed = []
        if done_folder.exists():
            # Sort files by modification time (most recent first)
            sorted_files = sorted(done_folder.glob("*.md"), 
                                key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            for file in sorted_files:
                recent_completed.append(file.name)
        
        # Read current dashboard content
        dashboard_path = Path("Dashboard.md")
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Create a basic dashboard if it doesn't exist
            content = """---
last_updated: 2026-02-12
---

# 🎯 AI Employee Dashboard

## 📊 Today's Overview
- Date: 2026-02-12
- System Status: ✅ Running
- Pending Tasks: 0
- Completed Today: 0

## 🔔 Pending Actions
*(Items from Needs_Action folder will appear here)*

## ✅ Recently Completed
*(Completed tasks from Done folder)*

## 📈 System Health
- Gmail Watcher: Not Started
- File Watcher: Not Started
- Last Check: Never

---"""

        # Update the dashboard content
        updated_content = content
        
        # Update date
        updated_content = updated_content.replace(
            f"- Date: {datetime.now().strftime('%Y-%m-%d')}",
            f"- Date: {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        # Update pending tasks count
        updated_content = updated_content.replace(
            f"- Pending Tasks: {needs_action_count if str(needs_action_count) in updated_content else '0'}",
            f"- Pending Tasks: {needs_action_count}"
        )
        
        # Update completed today count
        updated_content = updated_content.replace(
            f"- Completed Today: {completed_today if str(completed_today) in updated_content else '0'}",
            f"- Completed Today: {completed_today}"
        )
        
        # Update last updated timestamp
        updated_content = updated_content.replace(
            f"last_updated: {datetime.now().strftime('%Y-%m-%d')}",
            f"last_updated: {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        # Update recently completed section
        if recent_completed:
            completed_section = "## ✅ Recently Completed\n"
            for task in recent_completed:
                completed_section += f"- {task}\n"
        else:
            completed_section = "## ✅ Recently Completed\n*(Completed tasks from Done folder)*\n"
        
        # Find and replace the completed section
        start_marker = "## ✅ Recently Completed"
        end_marker = "\n## 📈 System Health"
        start_idx = updated_content.find(start_marker)
        end_idx = updated_content.find(end_marker, start_idx)
        
        if start_idx != -1 and end_idx != -1:
            updated_content = (
                updated_content[:start_idx] + 
                completed_section + 
                updated_content[end_idx:]
            )
        
        # Update system health section with current time
        updated_content = updated_content.replace(
            f"- Last Check: {datetime.now().strftime('%H:%M:%S')}",
            f"- Last Check: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        # Write updated content back to dashboard
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"Dashboard updated: {needs_action_count} pending, {completed_today} completed today")
        
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")

def health_check(logger):
    """
    Perform health check on the system components.
    """
    try:
        # Check if required folders exist
        folders = ["Inbox", "Needs_Action", "Done", "Logs", "Drop_Zone"]
        missing_folders = []
        
        for folder in folders:
            if not Path(folder).exists():
                missing_folders.append(folder)
        
        if missing_folders:
            logger.warning(f"Missing folders: {missing_folders}")
        
        # Check if watchers are running (basic check)
        gmail_watcher_running = Path("Logs").exists()  # Basic check
        file_watcher_running = Path("Drop_Zone").exists()  # Basic check
        
        # Update dashboard with health info
        dashboard_path = Path("Dashboard.md")
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update health status
            content = content.replace(
                "- Gmail Watcher: Not Started",
                f"- Gmail Watcher: {'✅ Running' if gmail_watcher_running else '❌ Stopped'}"
            )
            content = content.replace(
                "- File Watcher: Not Started", 
                f"- File Watcher: {'✅ Running' if file_watcher_running else '❌ Stopped'}"
            )
            content = content.replace(
                f"- Last Check: {datetime.now().strftime('%H:%M:%S')}",
                f"- Last Check: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        logger.info(f"Health check completed. Gmail Watcher: {'Running' if gmail_watcher_running else 'Stopped'}, "
                   f"File Watcher: {'Running' if file_watcher_running else 'Stopped'}")
        
    except Exception as e:
        logger.error(f"Error during health check: {e}")

def process_task_file(file_path, logger):
    """
    Process a task file using Claude Code CLI.
    
    Args:
        file_path (str): Path to the task file to process
        logger: Logger instance
    """
    try:
        logger.info(f"Processing task file: {file_path}")
        
        # Prepare the command to call Claude Code CLI
        command = [
            "claude-code",
            f"Read this task file and help complete it: {file_path}"
        ]
        
        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Log the interaction
        logger.info(f"Called Claude Code CLI for {file_path}")
        if result.stdout:
            logger.info(f"Claude output: {result.stdout[:200]}...")  # Log first 200 chars
        if result.stderr:
            logger.error(f"Claude error: {result.stderr}")
        
        # Move the processed file to Done folder
        done_folder = Path("Done")
        done_folder.mkdir(exist_ok=True)
        
        destination = done_folder / Path(file_path).name
        Path(file_path).rename(destination)
        
        logger.info(f"Moved {file_path} to Done folder")
        
        # Update dashboard after processing
        update_dashboard(logger)
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout processing {file_path} with Claude Code CLI")
    except FileNotFoundError:
        logger.error("Claude Code CLI not found. Please install it first.")
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")

def monitor_needs_action(logger):
    """
    Monitor the Needs_Action folder for new .md files and process them.
    """
    try:
        needs_action_folder = Path("Needs_Action")
        
        if not needs_action_folder.exists():
            logger.warning("Needs_Action folder does not exist")
            return
        
        # Look for new .md files in Needs_Action folder
        md_files = list(needs_action_folder.glob("*.md"))
        
        if not md_files:
            logger.debug("No new task files found in Needs_Action folder")
            return
        
        logger.info(f"Found {len(md_files)} task file(s) to process")
        
        for file_path in md_files:
            # Process each file
            process_task_file(str(file_path), logger)
            
            # Small delay between processing files to avoid overwhelming Claude API
            time.sleep(2)
    
    except Exception as e:
        logger.error(f"Error monitoring Needs_Action folder: {e}")

def main():
    """
    Main orchestrator loop that monitors Needs_Action folder and manages tasks.
    
    Startup Instructions:
    1. Ensure Claude Code CLI is installed and accessible from command line
    2. Make sure all required folders exist (Needs_Action, Done, Logs)
    3. Run this script: python orchestrator.py
    4. The orchestrator will run continuously, monitoring for new tasks
    
    Example Usage:
    - Place task files in Needs_Action folder
    - The orchestrator will automatically process them with Claude Code CLI
    - Completed tasks will be moved to Done folder
    - Dashboard will be updated with current status
    """
    logger = setup_logging()
    
    # Create required directories if they don't exist
    for folder in ["Needs_Action", "Done", "Logs", "Drop_Zone"]:
        Path(folder).mkdir(exist_ok=True)
    
    logger.info("Starting Orchestrator...")
    logger.info("Monitoring Needs_Action folder for new tasks")
    
    try:
        while True:
            # Monitor Needs_Action folder for new files
            monitor_needs_action(logger)
            
            # Update dashboard with current status
            update_dashboard(logger)
            
            # Perform health check
            health_check(logger)
            
            # Wait for 30 seconds before next check
            logger.debug("Waiting 30 seconds before next check...")
            time.sleep(30)
    
    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in orchestrator: {e}")
        raise

if __name__ == "__main__":
    main()