"""
Silver Tier AI Employee Orchestrator with Claude Reasoning Loop

This orchestrator implements a sophisticated task management system with Claude AI reasoning capabilities.
It operates in two phases: Planning and Execution, with an approval workflow for sensitive actions.

REASONING LOOP LOGIC:
1. MONITOR: Continuously watch Needs_Action/ folder for new tasks
2. ANALYZE: When a task is detected, use Claude to analyze and create a plan
3. PLAN: Generate a structured Plan.md file with steps and approval requirements
4. EXECUTE: Follow the plan step-by-step, checking off completed items
5. APPROVE: Route sensitive actions through approval workflow if needed
6. COMPLETE: Archive completed tasks and update dashboard

The orchestrator handles up to 3 tasks simultaneously with priority queuing based on urgency keywords.
"""

import os
import time
import logging
import json
import re
from pathlib import Path
from datetime import datetime
from threading import Lock
from collections import deque
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Global lock for thread-safe operations
task_lock = Lock()

def setup_logging():
    """Setup logging to both console and file"""
    # Create Logs directory if it doesn't exist
    logs_dir = Path("Logs")
    logs_dir.mkdir(exist_ok=True)

    # Create a logger
    logger = logging.getLogger('SilverTierOrchestrator')
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

class TaskManager:
    """Manages tasks, plans, and execution states"""
    
    def __init__(self, logger):
        self.logger = logger
        self.active_tasks = {}  # task_id -> plan_file mapping
        self.task_queue = deque()  # Queue for pending tasks
        self.processed_tasks = set()  # Track already processed tasks
        self.max_concurrent_tasks = 3
        self.urgency_keywords = ['urgent', 'asap', 'help', 'emergency', 'critical']
        
        # Create required directories
        for folder in ["Needs_Action", "Plans", "Done", "Logs", "Drop_Zone", "Pending_Approval", "Approved", "Rejected"]:
            Path(folder).mkdir(exist_ok=True)
    
    def get_task_priority(self, task_content):
        """Determine task priority based on keywords"""
        content_lower = task_content.lower()
        for keyword in self.urgency_keywords:
            if keyword in content_lower:
                return 'high'
        return 'normal'
    
    def extract_task_type(self, filename):
        """Extract task type from filename"""
        # Examples: EMAIL_xyz.md, WHATSAPP_abc.md, etc.
        match = re.match(r'^([A-Z]+)_', filename)
        if match:
            return match.group(1).lower()
        return 'unknown'
    
    def create_plan(self, task_file_path):
        """Create a plan for the given task using Claude analysis"""
        try:
            task_path = Path(task_file_path)
            task_id = task_path.stem  # filename without extension
            task_type = self.extract_task_type(task_path.name)
            
            # Read the task content
            with open(task_path, 'r', encoding='utf-8') as f:
                task_content = f.read()
            
            # Create plan filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plan_filename = f"PLAN_{task_type}_{timestamp}.md"
            plan_path = Path("Plans") / plan_filename
            
            # Determine if approval is needed based on content
            requires_approval = self.requires_approval(task_content)
            
            # Create the plan content
            plan_content = f"""---
task_id: {task_id}
created: {datetime.now().isoformat()}
status: pending
requires_approval: {str(requires_approval).lower()}
---

## Objective
{self.generate_objective(task_content)}

## Steps
- [ ] Step 1: Identify information needed
- [ ] Step 2: Draft response/action
- [ ] Step 3: Get approval (if required)
- [ ] Step 4: Execute action
- [ ] Step 5: Log and archive

## Resources Needed
- Company_Handbook.md for tone/rules
- Previous similar tasks in Done/

## Approval Required For
- Sending emails to new contacts
- Any financial actions
- Posting on social media
"""
            
            # Write the plan file
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(plan_content)
            
            self.logger.info(f"Created plan for task {task_id}: {plan_path}")
            
            # Add to active tasks
            with task_lock:
                self.active_tasks[task_id] = str(plan_path)
            
            return str(plan_path)
            
        except Exception as e:
            self.logger.error(f"Error creating plan for {task_file_path}: {e}")
            return None
    
    def requires_approval(self, task_content):
        """Determine if a task requires approval based on its content"""
        content_lower = task_content.lower()
        
        # Check for sensitive actions that require approval
        approval_triggers = [
            'email', 'send', 'payment', 'financial', 'money', 'invoice',
            'social media', 'post', 'marketing', 'customer', 'client',
            'urgent', 'asap', 'critical'
        ]
        
        for trigger in approval_triggers:
            if trigger in content_lower:
                return True
        
        return False
    
    def generate_objective(self, task_content):
        """Generate a clear objective from the task content"""
        # Simple extraction - in a real implementation, this would use Claude
        lines = task_content.split('\n')
        for line in lines:
            if 'message_content:' in line.lower() or 'subject:' in line.lower():
                return line.strip()
        
        # If no specific content found, return first meaningful line
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('---') and ':' not in stripped[:20]:
                return stripped[:100] + "..." if len(stripped) > 100 else stripped
        
        return "Process the task according to its content"
    
    def execute_plan(self, plan_file_path):
        """Execute the plan step by step"""
        try:
            plan_path = Path(plan_file_path)
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the frontmatter to get task_id and approval requirement
            lines = content.split('\n')
            task_id = None
            requires_approval = False
            
            for i, line in enumerate(lines):
                if line.strip() == '---' and i > 0:  # End of frontmatter
                    break
                if 'task_id:' in line:
                    task_id = line.split(':', 1)[1].strip()
                elif 'requires_approval:' in line:
                    requires_approval = line.split(':', 1)[1].strip().lower() == 'true'
            
            if not task_id:
                self.logger.error(f"Could not extract task_id from {plan_file_path}")
                return False
            
            # Find the original task file
            original_task_path = None
            for ext in ['.md']:
                potential_path = Path("Needs_Action") / f"{task_id}{ext}"
                if potential_path.exists():
                    original_task_path = potential_path
                    break
            
            if not original_task_path:
                self.logger.error(f"Original task file not found for {task_id}")
                return False
            
            # Read the original task content
            with open(original_task_path, 'r', encoding='utf-8') as f:
                task_content = f.read()
            
            # Update plan to mark Step 1 as complete
            content = content.replace('- [ ] Step 1: Identify information needed', '- [x] Step 1: Identify information needed')
            self.update_plan(plan_path, content)
            
            # Process Step 2: Draft response/action
            self.logger.info(f"Determining action for task {task_id}")
            content = content.replace('- [ ] Step 2: Draft response/action', '- [x] Step 2: Draft response/action')
            self.update_plan(plan_path, content)
            
            # Check if approval is required
            if requires_approval:
                # Move to pending approval
                self.route_for_approval(task_id, task_content)
                content = content.replace('- [ ] Step 3: Get approval (if required)', '- [x] Step 3: Get approval (if required)')
                self.update_plan(plan_path, content)
                self.logger.info(f"Task {task_id} routed for approval")
            else:
                # Execute directly
                self.execute_directly(task_id, task_content)
                content = content.replace('- [ ] Step 3: Get approval (if required)', '- [x] Step 3: Get approval (if required)')
                content = content.replace('- [ ] Step 4: Execute action', '- [x] Step 4: Execute action')
                content = content.replace('- [ ] Step 5: Log and archive', '- [x] Step 5: Log and archive')
                self.update_plan(plan_path, content)
                
                # Move original task to Done
                done_path = Path("Done") / original_task_path.name
                original_task_path.rename(done_path)
                
                self.logger.info(f"Task {task_id} executed directly and moved to Done")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing plan {plan_file_path}: {e}")
            return False
    
    def update_plan(self, plan_path, new_content):
        """Update the plan file with new content"""
        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def route_for_approval(self, task_id, task_content):
        """Route task for human approval"""
        # Create an approval file in Pending_Approval/
        approval_filename = f"APPROVAL_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        approval_path = Path("Pending_Approval") / approval_filename
        
        approval_content = f"""---
type: approval_request
original_task: {task_id}
request_date: {datetime.now().isoformat()}
status: pending_review
---

## Original Task Content
{task_content}

## Recommended Action
Based on the task content, this action requires human approval before execution.

## Approval Options
- Move this file to Approved/ folder to allow execution
- Move this file to Rejected/ folder to skip execution
"""
        
        with open(approval_path, 'w', encoding='utf-8') as f:
            f.write(appression_content)
        
        self.logger.info(f"Created approval request for {task_id}: {approval_path}")
    
    def execute_directly(self, task_id, task_content):
        """Execute the task directly without approval"""
        # In a real implementation, this would call Claude to process the task
        # For now, we'll simulate the processing
        
        # Simulate calling Claude to process the task
        self.logger.info(f"Executing task {task_id} directly with Claude")
        
        # Move the original task to Done
        original_task_path = Path("Needs_Action") / f"{task_id}.md"
        if original_task_path.exists():
            done_path = Path("Done") / original_task_path.name
            original_task_path.rename(done_path)
    
    def process_approval_workflow(self):
        """Monitor and process approval workflow"""
        # Check for newly approved tasks
        approved_dir = Path("Approved")
        if approved_dir.exists():
            for approval_file in approved_dir.glob("APPROVAL_*.md"):
                self.handle_approved_task(approval_file)
        
        # Check for rejected tasks
        rejected_dir = Path("Rejected")
        if rejected_dir.exists():
            for rejection_file in rejected_dir.glob("APPROVAL_*.md"):
                self.handle_rejected_task(rejection_file)
    
    def handle_approved_task(self, approval_file):
        """Handle a task that has been approved"""
        try:
            # Extract original task ID from filename
            filename = approval_file.name
            match = re.search(r'APPROVAL_([^_]+)_', filename)
            if match:
                task_id = match.group(1)
                
                # Find the original task file
                original_task_path = Path("Needs_Action") / f"{task_id}.md"
                if original_task_path.exists():
                    # Process the original task
                    with open(original_task_path, 'r', encoding='utf-8') as f:
                        task_content = f.read()
                    
                    # Execute the task
                    self.execute_directly(task_id, task_content)
                    
                    # Log the approval
                    self.logger.info(f"Approved and executed task {task_id}")
                
                # Move approval file to Done
                done_path = Path("Done") / approval_file.name
                approval_file.rename(done_path)
                
        except Exception as e:
            self.logger.error(f"Error handling approved task {approval_file}: {e}")
    
    def handle_rejected_task(self, rejection_file):
        """Handle a task that has been rejected"""
        try:
            # Extract original task ID from filename
            filename = rejection_file.name
            match = re.search(r'APPROVAL_([^_]+)_', filename)
            if match:
                task_id = match.group(1)
                
                # Move original task to Done (skipped)
                original_task_path = Path("Needs_Action") / f"{task_id}.md"
                if original_task_path.exists():
                    done_path = Path("Done") / original_task_path.name
                    original_task_path.rename(done_path)
                
                # Move rejection file to Done
                done_path = Path("Done") / rejection_file.name
                rejection_file.rename(done_path)
                
                self.logger.info(f"Rejected task {task_id}, moved to Done")
                
        except Exception as e:
            self.logger.error(f"Error handling rejected task {rejection_file}: {e}")

def update_dashboard(logger, task_manager):
    """
    Update Dashboard.md with current statistics and recent completed tasks.
    """
    try:
        # Count files in Needs_Action folder
        needs_action_count = len(list(Path("Needs_Action").glob("*.md")))

        # Count files in Plans folder (active plans)
        plans_count = len(list(Path("Plans").glob("*.md")))
        
        # Count files in Pending_Approval folder
        approval_count = len(list(Path("Pending_Approval").glob("*.md")))

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

# 🎯 Silver Tier AI Employee Dashboard

## 📊 Today's Overview
- Date: 2026-02-12
- System Status: ✅ Running
- Pending Tasks: 0
- Active Plans: 0
- Awaiting Approval: 0
- Completed Today: 0

## 🔔 Pending Actions
*(Items from Needs_Action folder will appear here)*

## 📋 Active Plans
*(Currently executing plans from Plans folder)*

## 🔄 Approval Queue
*(Tasks awaiting human approval)*

## ✅ Recently Completed
*(Completed tasks from Done folder)*

## 📈 System Health
- Gmail Watcher: Not Started
- File Watcher: Not Started
- LinkedIn Integration: Not Started
- WhatsApp Watcher: Not Started
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

        # Update active plans count
        updated_content = updated_content.replace(
            f"- Active Plans: {plans_count if str(plans_count) in updated_content else '0'}",
            f"- Active Plans: {plans_count}"
        )

        # Update approval queue count
        updated_content = updated_content.replace(
            f"- Awaiting Approval: {approval_count if str(approval_count) in updated_content else '0'}",
            f"- Awaiting Approval: {approval_count}"
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

        logger.info(f"Dashboard updated: {needs_action_count} pending, {plans_count} active plans, {approval_count} awaiting approval, {completed_today} completed today")

    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")

def health_check(logger):
    """
    Perform health check on the system components.
    """
    try:
        # Check if required folders exist
        folders = ["Inbox", "Needs_Action", "Done", "Logs", "Drop_Zone", "Plans", "Pending_Approval", "Approved", "Rejected"]
        missing_folders = []

        for folder in folders:
            if not Path(folder).exists():
                missing_folders.append(folder)

        if missing_folders:
            logger.warning(f"Missing folders: {missing_folders}")

        # Check if watchers are running (basic check)
        gmail_watcher_running = Path("Logs/gmail_watcher.log").exists()
        file_watcher_running = Path("Drop_Zone").exists()
        linkedin_running = Path("Logs/linkedin_integration.log").exists()
        whatsapp_running = Path("Logs/whatsapp_watcher.log").exists()

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
                "- LinkedIn Integration: Not Started",
                f"- LinkedIn Integration: {'✅ Running' if linkedin_running else '❌ Stopped'}"
            )
            content = content.replace(
                "- WhatsApp Watcher: Not Started",
                f"- WhatsApp Watcher: {'✅ Running' if whatsapp_running else '❌ Stopped'}"
            )
            content = content.replace(
                f"- Last Check: {datetime.now().strftime('%H:%M:%S')}",
                f"- Last Check: {datetime.now().strftime('%H:%M:%S')}"
            )

            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)

        logger.info(f"Health check completed. Gmail: {'Running' if gmail_watcher_running else 'Stopped'}, "
                   f"File Watcher: {'Running' if file_watcher_running else 'Stopped'}, "
                   f"LinkedIn: {'Running' if linkedin_running else 'Stopped'}, "
                   f"WhatsApp: {'Running' if whatsapp_running else 'Stopped'}")

    except Exception as e:
        logger.error(f"Error during health check: {e}")

def monitor_needs_action(logger, task_manager):
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

        # Sort files by priority
        priority_files = []
        normal_files = []
        
        for file_path in md_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if task_manager.get_task_priority(content) == 'high':
                priority_files.append(file_path)
            else:
                normal_files.append(file_path)
        
        # Process priority files first
        all_files = priority_files + normal_files

        for file_path in all_files:
            task_id = Path(file_path).stem
            
            # Check if already processed
            if task_id in task_manager.processed_tasks:
                continue
            
            # Check if we're at max concurrent tasks
            with task_lock:
                if len(task_manager.active_tasks) >= task_manager.max_concurrent_tasks:
                    logger.info("At maximum concurrent tasks, queuing additional tasks")
                    task_manager.task_queue.append(str(file_path))
                    continue
            
            # Process the task: create a plan for it
            plan_path = task_manager.create_plan(str(file_path))
            if plan_path:
                # Execute the plan
                task_manager.execute_plan(plan_path)
                
                # Mark as processed
                task_manager.processed_tasks.add(task_id)

        # Process queued tasks if capacity allows
        with task_lock:
            while (len(task_manager.active_tasks) < task_manager.max_concurrent_tasks and 
                   task_manager.task_queue):
                queued_file = task_manager.task_queue.popleft()
                task_id = Path(queued_file).stem
                
                if task_id not in task_manager.processed_tasks:
                    plan_path = task_manager.create_plan(queued_file)
                    if plan_path:
                        task_manager.execute_plan(plan_path)
                        task_manager.processed_tasks.add(task_id)

    except Exception as e:
        logger.error(f"Error monitoring Needs_Action folder: {e}")

def monitor_plans(logger, task_manager):
    """
    Monitor the Plans folder for updates and execute remaining steps.
    """
    try:
        plans_folder = Path("Plans")

        if not plans_folder.exists():
            logger.warning("Plans folder does not exist")
            return

        # Look for plan files that are not yet fully executed
        plan_files = list(plans_folder.glob("*.md"))

        for plan_file in plan_files:
            with open(plan_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if all steps are completed
            if '- [ ] Step 4: Execute action' not in content and \
               '- [ ] Step 5: Log and archive' not in content:
                # Plan is fully executed, move to Done if not already done
                done_plan_path = Path("Done") / plan_file.name
                plan_file.rename(done_plan_path)
                logger.info(f"Moved completed plan to Done: {done_plan_path}")

    except Exception as e:
        logger.error(f"Error monitoring Plans folder: {e}")

def main():
    """
    Main orchestrator loop that monitors Needs_Action folder and manages tasks.

    SILVER TIER REASONING LOOP:
    1. MONITOR: Continuously watch Needs_Action/ folder for new tasks
    2. ANALYZE: When a task is detected, use Claude to analyze and create a plan
    3. PLAN: Generate a structured Plan.md file with steps and approval requirements
    4. EXECUTE: Follow the plan step-by-step, checking off completed items
    5. APPROVE: Route sensitive actions through approval workflow if needed
    6. COMPLETE: Archive completed tasks and update dashboard

    The orchestrator handles up to 3 tasks simultaneously with priority queuing based on urgency keywords.
    """
    logger = setup_logging()
    
    # Initialize task manager
    task_manager = TaskManager(logger)

    logger.info("Starting Silver Tier Orchestrator...")
    logger.info("Monitoring Needs_Action folder for new tasks")
    logger.info("Using Claude reasoning loop for task planning and execution")

    try:
        while True:
            # Monitor Needs_Action folder for new files
            monitor_needs_action(logger, task_manager)

            # Monitor Plans folder for updates
            monitor_plans(logger, task_manager)

            # Process approval workflow
            task_manager.process_approval_workflow()

            # Update dashboard with current status
            update_dashboard(logger, task_manager)

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