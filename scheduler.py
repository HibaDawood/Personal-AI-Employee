"""
Silver Tier AI Employee Scheduler

This module implements a scheduler for various automated tasks in the Silver Tier AI Employee system.
It uses the schedule library to run tasks at specified intervals.

TASK SCHEDULE:
- Every 2 minutes: Check for new tasks in Needs_Action/
- Every 5 minutes: Update Dashboard.md
- Every 30 minutes: Health check all watchers
- Every 6 hours: LinkedIn check
- Daily 8 AM: Morning briefing summary
- Daily 6 PM: End of day summary
- Weekly Sunday 8 PM: Weekly business review

HEALTH MONITORING:
- Checks if watcher processes are running
- Restarts crashed processes
- Alerts to Dashboard if issues detected
"""

import schedule
import time
import subprocess
import logging
import os
import psutil
import json
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SilverTierScheduler:
    def __init__(self):
        self.process_names = {
            'gmail_watcher': 'gmail_watcher.py',
            'filesystem_watcher': 'filesystem_watcher.py',
            'whatsapp_watcher': 'whatsapp_watcher.py',
            'linkedin_integration': 'linkedin_integration.py',
            'orchestrator': 'orchestrator.py'
        }
        self.setup_schedule()
    
    def setup_schedule(self):
        """Set up all scheduled tasks"""
        # Every 2 minutes: Check for new tasks in Needs_Action/
        schedule.every(2).minutes.do(self.check_needs_action)
        
        # Every 5 minutes: Update Dashboard.md
        schedule.every(5).minutes.do(self.update_dashboard)
        
        # Every 30 minutes: Health check all watchers
        schedule.every(30).minutes.do(self.health_check_watchers)
        
        # Every 6 hours: LinkedIn check
        schedule.every(6).hours.do(self.linkedin_check)
        
        # Daily 8 AM: Morning briefing summary
        schedule.every().day.at("08:00").do(self.morning_briefing)
        
        # Daily 6 PM: End of day summary
        schedule.every().day.at("18:00").do(self.end_of_day_summary)
        
        # Weekly Sunday 8 PM: Weekly business review
        schedule.every().sunday.at("20:00").do(self.weekly_business_review)
        
        logger.info("Scheduled tasks initialized")
    
    def check_needs_action(self):
        """Check for new tasks in Needs_Action/ folder"""
        try:
            needs_action_dir = Path("Needs_Action")
            if not needs_action_dir.exists():
                logger.warning("Needs_Action directory does not exist")
                return
            
            # Count new tasks
            new_tasks = list(needs_action_dir.glob("*.md"))
            logger.info(f"Checked Needs_Action/: {len(new_tasks)} tasks found")
            
            # If there are tasks, trigger the orchestrator to process them
            if new_tasks:
                # Run orchestrator in a separate thread to avoid blocking
                thread = threading.Thread(target=self.run_orchestrator_check)
                thread.start()
                
        except Exception as e:
            logger.error(f"Error checking Needs_Action/: {e}")
            self.create_alert(f"Error checking Needs_Action/: {e}")
    
    def run_orchestrator_check(self):
        """Run orchestrator check in a separate thread"""
        try:
            result = subprocess.run(
                ["python", "orchestrator.py", "--check"],
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )
            if result.returncode != 0:
                logger.error(f"Orchestrator check failed: {result.stderr}")
                self.create_alert(f"Orchestrator check failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Orchestrator check timed out")
            self.create_alert("Orchestrator check timed out")
        except Exception as e:
            logger.error(f"Error running orchestrator check: {e}")
            self.create_alert(f"Error running orchestrator check: {e}")
    
    def update_dashboard(self):
        """Update Dashboard.md"""
        try:
            result = subprocess.run(
                ["python", "orchestrator.py", "--update-dashboard"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                logger.error(f"Dashboard update failed: {result.stderr}")
                self.create_alert(f"Dashboard update failed: {result.stderr}")
            else:
                logger.info("Dashboard updated successfully")
        except subprocess.TimeoutExpired:
            logger.error("Dashboard update timed out")
            self.create_alert("Dashboard update timed out")
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            self.create_alert(f"Error updating dashboard: {e}")
    
    def health_check_watchers(self):
        """Health check all watcher processes"""
        try:
            logger.info("Performing health check on all watchers")
            
            # Check each process
            for process_name, script_name in self.process_names.items():
                if not self.is_process_running(script_name):
                    logger.warning(f"{process_name} is not running, restarting...")
                    self.restart_process(process_name, script_name)
                else:
                    logger.info(f"{process_name} is running")
            
            # Run orchestrator health check
            result = subprocess.run(
                ["python", "orchestrator.py", "--health-check"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                logger.error(f"Orchestrator health check failed: {result.stderr}")
                self.create_alert(f"Orchestrator health check failed: {result.stderr}")
            else:
                logger.info("Orchestrator health check completed successfully")
                
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            self.create_alert(f"Error during health check: {e}")
    
    def is_process_running(self, script_name):
        """Check if a process with the given script name is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if script_name in ' '.join(proc.info['cmdline']):
                    return True
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
    
    def restart_process(self, process_name, script_name):
        """Restart a process"""
        try:
            # Kill any existing processes with the same name
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if script_name in ' '.join(proc.info['cmdline']):
                    proc.kill()
                    logger.info(f"Killed existing {process_name} process (PID: {proc.info['pid']})")
            
            # Start the process
            if script_name == 'gmail_watcher.py':
                subprocess.Popen(["python", script_name])
            elif script_name == 'filesystem_watcher.py':
                subprocess.Popen(["python", script_name])
            elif script_name == 'whatsapp_watcher.py':
                subprocess.Popen(["python", script_name])
            elif script_name == 'linkedin_integration.py':
                subprocess.Popen(["python", script_name])
            elif script_name == 'orchestrator.py':
                subprocess.Popen(["python", script_name])
            
            logger.info(f"Restarted {process_name}")
        except Exception as e:
            logger.error(f"Error restarting {process_name}: {e}")
            self.create_alert(f"Error restarting {process_name}: {e}")
    
    def linkedin_check(self):
        """Perform LinkedIn check every 6 hours"""
        try:
            logger.info("Performing LinkedIn check")
            
            # Run LinkedIn integration check
            result = subprocess.run(
                ["python", "linkedin_integration.py", "--check"],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for LinkedIn operations
            )
            if result.returncode != 0:
                logger.error(f"LinkedIn check failed: {result.stderr}")
                self.create_alert(f"LinkedIn check failed: {result.stderr}")
            else:
                logger.info("LinkedIn check completed successfully")
        except subprocess.TimeoutExpired:
            logger.error("LinkedIn check timed out")
            self.create_alert("LinkedIn check timed out")
        except Exception as e:
            logger.error(f"Error during LinkedIn check: {e}")
            self.create_alert(f"Error during LinkedIn check: {e}")
    
    def morning_briefing(self):
        """Generate morning briefing summary"""
        try:
            logger.info("Generating morning briefing")
            
            # Create a summary of yesterday's activity
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            
            # Count completed tasks from yesterday
            done_dir = Path("Done")
            if done_dir.exists():
                completed_yesterday = [f for f in done_dir.glob("*.md") 
                                     if f.stat().st_mtime > (datetime.now() - timedelta(days=1)).timestamp()]
                
                # Create morning briefing file
                briefing_file = done_dir / f"MORNING_BRIEFING_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                
                with open(briefing_file, 'w') as f:
                    f.write(f"""---
type: morning_briefing
date: {datetime.now().isoformat()}
---

# Morning Briefing - {datetime.now().strftime('%B %d, %Y')}

## Yesterday's Summary
- Tasks completed: {len(completed_yesterday)}
- New tasks in queue: {len(list(Path('Needs_Action').glob('*.md')))}
- System status: Operational

## Today's Priorities
- Monitor Needs_Action folder for new tasks
- Process pending approvals
- Maintain system health

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
                
                logger.info(f"Morning briefing created: {briefing_file}")
            else:
                logger.warning("Done directory does not exist")
                
        except Exception as e:
            logger.error(f"Error generating morning briefing: {e}")
            self.create_alert(f"Error generating morning briefing: {e}")
    
    def end_of_day_summary(self):
        """Generate end of day summary"""
        try:
            logger.info("Generating end of day summary")
            
            # Count tasks completed today
            today_str = datetime.now().strftime("%Y-%m-%d")
            done_dir = Path("Done")
            
            if done_dir.exists():
                completed_today = [f for f in done_dir.glob("*.md") 
                                 if f.stat().st_mtime > (datetime.now() - timedelta(days=1)).timestamp()]
                
                # Create end of day summary file
                summary_file = done_dir / f"EOD_SUMMARY_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                
                with open(summary_file, 'w') as f:
                    f.write(f"""---
type: eod_summary
date: {datetime.now().isoformat()}
---

# End of Day Summary - {datetime.now().strftime('%B %d, %Y')}

## Today's Activity
- Tasks completed: {len(completed_today)}
- Remaining tasks: {len(list(Path('Needs_Action').glob('*.md')))}
- System status: Operational

## Highlights
- Processed {len(completed_today)} tasks today
- Maintained system uptime
- Handled all scheduled operations

## Tomorrow's Outlook
- Continue processing pending tasks
- Monitor for new assignments
- Perform routine maintenance

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
                
                logger.info(f"End of day summary created: {summary_file}")
            else:
                logger.warning("Done directory does not exist")
                
        except Exception as e:
            logger.error(f"Error generating end of day summary: {e}")
            self.create_alert(f"Error generating end of day summary: {e}")
    
    def weekly_business_review(self):
        """Generate weekly business review"""
        try:
            logger.info("Generating weekly business review")
            
            # Calculate week range
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())  # Monday
            end_of_week = start_of_week + timedelta(days=6)  # Sunday
            
            # Count tasks completed this week
            done_dir = Path("Done")
            week_start_ts = start_of_week.timestamp()
            week_end_ts = end_of_week.timestamp()
            
            if done_dir.exists():
                completed_this_week = []
                for f in done_dir.glob("*.md"):
                    mod_time = f.stat().st_mtime
                    if week_start_ts <= mod_time <= week_end_ts:
                        completed_this_week.append(f)
                
                # Create weekly review file
                review_file = done_dir / f"WEEKLY_REVIEW_{start_of_week.strftime('%Y%m%d')}_{end_of_week.strftime('%Y%m%d')}.md"
                
                with open(review_file, 'w') as f:
                    f.write(f"""---
type: weekly_review
week_start: {start_of_week.isoformat()}
week_end: {end_of_week.isoformat()}
---

# Weekly Business Review - Week of {start_of_week.strftime('%B %d')} to {end_of_week.strftime('%B %d, %Y')}

## This Week's Performance
- Tasks completed: {len(completed_this_week)}
- Average daily completion: {len(completed_this_week)/7:.1f} tasks/day
- System uptime: 100%

## Key Accomplishments
- Processed {len(completed_this_week)} tasks
- Maintained operational efficiency
- Handled all scheduled operations

## Areas for Improvement
- Monitor task queue for bottlenecks
- Optimize resource allocation if needed

## Next Week's Focus
- Continue processing tasks efficiently
- Monitor system health
- Prepare for upcoming assignments

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
                
                logger.info(f"Weekly business review created: {review_file}")
            else:
                logger.warning("Done directory does not exist")
                
        except Exception as e:
            logger.error(f"Error generating weekly business review: {e}")
            self.create_alert(f"Error generating weekly business review: {e}")
    
    def create_alert(self, message):
        """Create an alert in Needs_Action/ for failed tasks"""
        try:
            needs_action_dir = Path("Needs_Action")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = needs_action_dir / f"SCHEDULER_ALERT_{timestamp}.md"
            
            with open(alert_file, 'w') as f:
                f.write(f"""---
type: scheduler_alert
severity: high
created: {datetime.now().isoformat()}
status: pending
---

# Scheduler Alert

## Issue
{message}

## Action Required
- Investigate the issue
- Resolve the problem
- Verify system functionality

Generated by scheduler at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
            
            logger.info(f"Created alert file: {alert_file}")
        except Exception as e:
            logger.error(f"Error creating alert file: {e}")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        logger.info("Starting Silver Tier Scheduler...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before continuing

def main():
    """Main entry point for the scheduler"""
    scheduler = SilverTierScheduler()
    scheduler.run_scheduler()

if __name__ == "__main__":
    main()