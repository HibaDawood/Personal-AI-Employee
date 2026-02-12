"""
Silver Tier AI Employee - Approval Manager

This module handles the human-in-the-loop approval workflow for sensitive actions.
It creates approval requests, monitors for approvals/rejections, and manages the entire lifecycle.

FEATURES:
1. APPROVAL REQUEST CREATION: Creates standardized approval request files
2. APPROVAL WATCHER: Monitors Approved/ folder and executes actions
3. REJECTION HANDLER: Processes rejected requests and learns from them
4. EXPIRY HANDLER: Auto-rejects requests after 24 hours
5. NOTIFICATION SYSTEM: Alerts when approvals are needed
6. APPROVAL ANALYTICS: Tracks approval statistics and patterns
"""

import os
import json
import time
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
import re

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'approval_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ApprovalManager:
    def __init__(self):
        self.pending_approval_dir = Path("Pending_Approval")
        self.approved_dir = Path("Approved")
        self.rejected_dir = Path("Rejected")
        self.done_dir = Path("Done")
        
        # Create directories if they don't exist
        self.pending_approval_dir.mkdir(exist_ok=True)
        self.approved_dir.mkdir(exist_ok=True)
        self.rejected_dir.mkdir(exist_ok=True)
        self.done_dir.mkdir(exist_ok=True)
        
        # Approval expiry time (24 hours)
        self.expiry_hours = 24
        
        # Initialize analytics
        self.analytics_file = logs_dir / "approval_stats.json"
        self.init_analytics()
    
    def init_analytics(self):
        """Initialize approval analytics file"""
        if not self.analytics_file.exists():
            initial_stats = {
                "total_requests": 0,
                "approved_requests": 0,
                "rejected_requests": 0,
                "expired_requests": 0,
                "average_response_time": 0,  # in seconds
                "action_types": {},
                "rejection_reasons": {},
                "approval_rate": 0
            }
            with open(self.analytics_file, 'w') as f:
                json.dump(initial_stats, f, indent=2)
    
    def load_analytics(self):
        """Load current analytics"""
        try:
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading analytics: {e}")
            return {}
    
    def save_analytics(self, stats):
        """Save analytics to file"""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving analytics: {e}")
    
    def create_approval_request(self, action_type, details, priority="normal", risks=None):
        """
        Create an approval request file in Pending_Approval/ folder
        
        Args:
            action_type (str): Type of action (email_send, payment, social_post, etc.)
            details (str): Specific details of the action
            priority (str): Priority level (normal, high)
            risks (str): Potential risks associated with the action
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            expires_at = (datetime.now() + timedelta(hours=self.expiry_hours)).isoformat()
            
            # Create filename
            filename = f"{action_type.upper()}_REQ_{timestamp}.md"
            filepath = self.pending_approval_dir / filename
            
            # Prepare risks section
            risks_section = f"## Risks\n{risks}\n" if risks else "## Risks\nNone identified.\n"
            
            # Create content
            content = f"""---
type: approval_request
action: {action_type}
created: {datetime.now().isoformat()}
expires: {expires_at}
status: pending
priority: {priority}
---

## Action Details
{details}

{risks_section}

## To Approve
Move this file to Approved/ folder

## To Reject
Move this file to Rejected/ folder

## To Modify
Edit this file and move to Approved/
"""
            
            # Write the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Created approval request: {filepath}")
            
            # Update analytics
            self.update_analytics_on_creation(action_type)
            
            # Send notification
            self.send_notification(f"New {action_type} approval request: {filename}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error creating approval request: {e}")
            return None
    
    def update_analytics_on_creation(self, action_type):
        """Update analytics when a new request is created"""
        try:
            stats = self.load_analytics()
            stats["total_requests"] = stats.get("total_requests", 0) + 1
            
            # Update action type count
            action_counts = stats.get("action_types", {})
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            stats["action_types"] = action_counts
            
            self.save_analytics(stats)
        except Exception as e:
            logger.error(f"Error updating analytics on creation: {e}")
    
    def update_analytics_on_approval(self, response_time):
        """Update analytics when a request is approved"""
        try:
            stats = self.load_analytics()
            stats["approved_requests"] = stats.get("approved_requests", 0) + 1
            stats["approval_rate"] = round(
                (stats.get("approved_requests", 0) / max(stats.get("total_requests", 1), 1)) * 100, 2
            )
            
            # Update average response time
            current_avg = stats.get("average_response_time", 0)
            total_approved = stats.get("approved_requests", 1)
            new_avg = ((current_avg * (total_approved - 1)) + response_time) / total_approved
            stats["average_response_time"] = new_avg
            
            self.save_analytics(stats)
        except Exception as e:
            logger.error(f"Error updating analytics on approval: {e}")
    
    def update_analytics_on_rejection(self, rejection_reason="Not specified"):
        """Update analytics when a request is rejected"""
        try:
            stats = self.load_analytics()
            stats["rejected_requests"] = stats.get("rejected_requests", 0) + 1
            stats["approval_rate"] = round(
                (stats.get("approved_requests", 0) / max(stats.get("total_requests", 1), 1)) * 100, 2
            )
            
            # Update rejection reasons
            reasons = stats.get("rejection_reasons", {})
            reasons[rejection_reason] = reasons.get(rejection_reason, 0) + 1
            stats["rejection_reasons"] = reasons
            
            self.save_analytics(stats)
        except Exception as e:
            logger.error(f"Error updating analytics on rejection: {e}")
    
    def update_analytics_on_expiry(self):
        """Update analytics when a request expires"""
        try:
            stats = self.load_analytics()
            stats["expired_requests"] = stats.get("expired_requests", 0) + 1
            self.save_analytics(stats)
        except Exception as e:
            logger.error(f"Error updating analytics on expiry: {e}")
    
    def execute_approved_action(self, approval_file):
        """Execute an approved action based on its type"""
        try:
            with open(approval_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the frontmatter to get action type
            lines = content.split('\n')
            action_type = None
            
            for i, line in enumerate(lines):
                if line.strip() == '---' and i > 0:  # End of frontmatter
                    break
                if 'action:' in line:
                    action_type = line.split(':', 1)[1].strip()
                    break
            
            if not action_type:
                logger.error(f"Could not determine action type from {approval_file}")
                return False
            
            logger.info(f"Executing approved {action_type} action from {approval_file}")
            
            # Execute action based on type
            success = False
            if action_type == "email_send":
                success = self.execute_email_send(content)
            elif action_type == "social_post":
                success = self.execute_social_post(content)
            elif action_type == "payment":
                success = self.execute_payment(content)
            else:
                success = self.execute_generic_action(action_type, content)
            
            if success:
                # Calculate response time
                created_match = re.search(r'created: ([^\n]+)', content)
                if created_match:
                    created_time = datetime.fromisoformat(created_match.group(1).replace('Z', '+00:00'))
                    response_time = (datetime.now() - created_time).total_seconds()
                    self.update_analytics_on_approval(response_time)
                
                logger.info(f"Successfully executed {action_type} action")
                
                # Move to Done folder
                done_path = self.done_dir / approval_file.name
                approval_file.rename(done_path)
                
                return True
            else:
                logger.error(f"Failed to execute {action_type} action")
                return False
                
        except Exception as e:
            logger.error(f"Error executing approved action: {e}")
            return False
    
    def execute_email_send(self, content):
        """Execute email send action"""
        try:
            # Extract email details from content
            to_match = re.search(r'To: ([^\n]+)', content)
            subject_match = re.search(r'Subject: ([^\n]+)', content)
            body_match = re.search(r'Body: ([\s\S]*?)(?=##|\Z)', content)
            
            if not to_match or not subject_match:
                logger.error("Could not extract email details from content")
                return False
            
            to = to_match.group(1).strip()
            subject = subject_match.group(1).strip()
            body = body_match.group(1).strip() if body_match else ""
            
            # Call email MCP server to send email
            # In a real implementation, this would call the MCP server
            logger.info(f"Sending email to {to} with subject '{subject}'")
            
            # Simulate calling the email MCP server
            # In a real implementation, you would use the MCP client to call the email server
            # For now, we'll simulate success
            return True
            
        except Exception as e:
            logger.error(f"Error executing email send: {e}")
            return False
    
    def execute_social_post(self, content):
        """Execute social media post action"""
        try:
            # Extract post details from content
            platform_match = re.search(r'Platform: ([^\n]+)', content)
            post_content_match = re.search(r'Content: ([\s\S]*?)(?=##|\Z)', content)
            
            if not platform_match:
                logger.error("Could not extract platform from content")
                return False
            
            platform = platform_match.group(1).strip()
            post_content = post_content_match.group(1).strip() if post_content_match else ""
            
            logger.info(f"Posting to {platform}: {post_content[:50]}...")
            
            # In a real implementation, this would call the appropriate social media MCP
            # For now, we'll simulate success
            return True
            
        except Exception as e:
            logger.error(f"Error executing social post: {e}")
            return False
    
    def execute_payment(self, content):
        """Execute payment action"""
        try:
            # Extract payment details from content
            amount_match = re.search(r'Amount: ([^\n]+)', content)
            recipient_match = re.search(r'Recipient: ([^\n]+)', content)
            
            if not amount_match or not recipient_match:
                logger.error("Could not extract payment details from content")
                return False
            
            amount = amount_match.group(1).strip()
            recipient = recipient_match.group(1).strip()
            
            logger.info(f"Processing payment of {amount} to {recipient}")
            
            # In a real implementation, this would call the payment processing system
            # For now, we'll simulate success
            return True
            
        except Exception as e:
            logger.error(f"Error executing payment: {e}")
            return False
    
    def execute_generic_action(self, action_type, content):
        """Execute a generic action"""
        try:
            logger.info(f"Executing generic action: {action_type}")
            # In a real implementation, this would handle other action types
            return True
        except Exception as e:
            logger.error(f"Error executing generic action: {e}")
            return False
    
    def handle_rejected_request(self, rejection_file):
        """Handle a rejected request"""
        try:
            with open(rejection_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract action type
            action_type_match = re.search(r'action: ([^\n]+)', content)
            action_type = action_type_match.group(1).strip() if action_type_match else "unknown"
            
            logger.info(f"Handling rejected {action_type} request: {rejection_file.name}")
            
            # Update analytics
            self.update_analytics_on_rejection()
            
            # Learn from rejection by updating Company_Handbook.md
            self.learn_from_rejection(content, action_type)
            
            # Move to Done folder
            done_path = self.done_dir / rejection_file.name
            rejection_file.rename(done_path)
            
            logger.info(f"Handled rejected request: {rejection_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling rejected request: {e}")
            return False
    
    def learn_from_rejection(self, content, action_type):
        """Learn from rejection by updating Company_Handbook.md"""
        try:
            handbook_path = Path("Company_Handbook.md")
            
            # Read current handbook
            handbook_content = ""
            if handbook_path.exists():
                with open(handbook_path, 'r', encoding='utf-8') as f:
                    handbook_content = f.read()
            
            # Add rejection learning to handbook
            learning_section = f"\n\n## Rejection Learning - {datetime.now().strftime('%Y-%m-%d')}\n"
            learning_section += f"Action Type: {action_type}\n"
            learning_section += f"Content: {content[:200]}...\n"
            learning_section += "Lesson: This type of request was rejected. Consider additional validation before resubmission.\n"
            
            # Append to handbook
            with open(handbook_path, 'a', encoding='utf-8') as f:
                f.write(learning_section)
            
            logger.info(f"Learned from rejection and updated Company_Handbook.md")
            
        except Exception as e:
            logger.error(f"Error learning from rejection: {e}")
    
    def check_expired_requests(self):
        """Check for and auto-reject expired requests"""
        try:
            logger.info("Checking for expired approval requests...")
            
            for approval_file in self.pending_approval_dir.glob("*.md"):
                with open(approval_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract expiration time
                expires_match = re.search(r'expires: ([^\n]+)', content)
                if expires_match:
                    expires_str = expires_match.group(1).strip()
                    try:
                        expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                        
                        if datetime.now() >= expires_at:
                            logger.info(f"Request {approval_file.name} has expired, auto-rejecting...")
                            
                            # Update analytics
                            self.update_analytics_on_expiry()
                            
                            # Add expiration note to content
                            expired_content = content + f"\n\n## Auto-Rejected\nReason: Request expired at {expires_str}\nAuto-rejected by system at {datetime.now().isoformat()}\n"
                            
                            # Write updated content back
                            with open(approval_file, 'w', encoding='utf-8') as f:
                                f.write(expired_content)
                            
                            # Move to Rejected folder
                            rejected_path = self.rejected_dir / approval_file.name
                            approval_file.rename(rejected_path)
                            
                            logger.info(f"Auto-rejected expired request: {approval_file.name}")
                    except ValueError:
                        logger.error(f"Invalid expiration date format in {approval_file.name}")
            
        except Exception as e:
            logger.error(f"Error checking expired requests: {e}")
    
    def send_notification(self, message):
        """Send notification about pending approval"""
        try:
            logger.info(f"NOTIFICATION: {message}")
            
            # Try to send desktop notification if possible
            try:
                # Linux
                subprocess.run(['notify-send', 'Silver Tier AI', message], timeout=5)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                try:
                    # macOS
                    subprocess.run(['osascript', '-e', f'display notification "{message}" with title "Silver Tier AI"'], timeout=5)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    try:
                        # Windows
                        subprocess.run([
                            'powershell', '-command',
                            f'Add-Type -AssemblyName System.Windows.Forms; '
                            f'$global:balloon = New-Object System.Windows.Forms.NotifyIcon; '
                            f'$path = (Get-Process -id $pid).Path; '
                            f'$balloon.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon($path); '
                            f'$balloon.BalloonTipText = "{message}"; '
                            f'$balloon.BalloonTipTitle = "Silver Tier AI"; '
                            f'$balloon.Visible = $true; '
                            f'$balloon.ShowBalloonTip(5000);'
                        ], timeout=5)
                    except:
                        # If all notification methods fail, just log it
                        pass
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_pending_approval_count(self):
        """Get count of pending approval requests"""
        return len(list(self.pending_approval_dir.glob("*.md")))
    
    def monitor_approvals(self):
        """Monitor Approved/ folder for new approvals"""
        try:
            approved_files = list(self.approved_dir.glob("*.md"))
            
            for approval_file in approved_files:
                logger.info(f"Processing approved request: {approval_file.name}")
                
                success = self.execute_approved_action(approval_file)
                
                if not success:
                    logger.error(f"Failed to execute approved action: {approval_file.name}")
                    # Move to Done even if execution failed
                    done_path = self.done_dir / approval_file.name
                    approval_file.rename(done_path)
        
        except Exception as e:
            logger.error(f"Error monitoring approvals: {e}")
    
    def monitor_rejections(self):
        """Monitor Rejected/ folder for new rejections"""
        try:
            rejected_files = list(self.rejected_dir.glob("*.md"))
            
            for rejection_file in rejected_files:
                logger.info(f"Processing rejected request: {rejection_file.name}")
                
                success = self.handle_rejected_request(rejection_file)
                
                if not success:
                    logger.error(f"Failed to handle rejected request: {rejection_file.name}")
        
        except Exception as e:
            logger.error(f"Error monitoring rejections: {e}")
    
    def run_monitoring_loop(self):
        """Run the main monitoring loop"""
        logger.info("Starting Approval Manager monitoring loop...")
        
        while True:
            try:
                # Check for expired requests
                self.check_expired_requests()
                
                # Monitor for approvals
                self.monitor_approvals()
                
                # Monitor for rejections
                self.monitor_rejections()
                
                # Update dashboard with pending count
                pending_count = self.get_pending_approval_count()
                self.update_dashboard_count(pending_count)
                
                # Sleep before next iteration
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Approval Manager stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def update_dashboard_count(self, pending_count):
        """Update dashboard with pending approval count"""
        try:
            dashboard_path = Path("Dashboard.md")
            if dashboard_path.exists():
                with open(dashboard_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Update the pending approval count in the dashboard
                # Look for a line that mentions approval queue
                import re
                pattern = r'(- Awaiting Approval: )\d+'
                replacement = f'\\g<1>{pending_count}'
                updated_content = re.sub(pattern, replacement, content)
                
                with open(dashboard_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                    
        except Exception as e:
            logger.error(f"Error updating dashboard count: {e}")

def main():
    """Main entry point for the approval manager"""
    approval_manager = ApprovalManager()
    
    # If command line arguments are provided, create a sample approval request
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "create_sample":
            if len(sys.argv) >= 4:
                action_type = sys.argv[2]
                details = sys.argv[3]
                priority = sys.argv[4] if len(sys.argv) > 4 else "normal"
                
                approval_manager.create_approval_request(
                    action_type=action_type,
                    details=details,
                    priority=priority
                )
                return
            else:
                print("Usage: python approval_manager.py create_sample <action_type> <details> [priority]")
                return
    
    # Start the monitoring loop
    approval_manager.run_monitoring_loop()

if __name__ == "__main__":
    main()