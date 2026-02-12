"""
LinkedIn Integration for Silver Tier AI Employee

This module provides two main functions:
1. LinkedIn Watcher: Monitors LinkedIn for new connection requests, messages, and job opportunities
2. LinkedIn Auto-Poster: Posts approved content to LinkedIn with rate limiting

Setup Instructions:
1. Create a .env file with your LinkedIn credentials:
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
2. First run: Browser will open for manual login and 2FA if enabled
3. Subsequent runs: Session will be restored from linkedin_session/ folder
4. For posting: Create posts in Pending_Approval/ folder with proper metadata

WARNING: Using automation tools with LinkedIn may violate LinkedIn's Terms of Service.
Use this script responsibly and at your own risk. Excessive automation may result in account restrictions.

Dependencies:
- Playwright: pip install playwright
- Also run: playwright install chromium
"""

import asyncio
import json
import os
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/linkedin_integration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class LinkedInIntegration:
    def __init__(self):
        self.session_dir = Path("linkedin_session")
        self.needs_action_dir = Path("Needs_Action")
        self.pending_approval_dir = Path("Pending_Approval")
        self.approved_dir = Path("Approved")
        self.logs_dir = Path("Logs")
        self.browser = None
        self.page = None
        
        # Create directories if they don't exist
        self.session_dir.mkdir(exist_ok=True)
        self.needs_action_dir.mkdir(exist_ok=True)
        self.pending_approval_dir.mkdir(exist_ok=True)
        self.approved_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Track daily post count
        self.daily_post_count = 0
        self.post_reset_date = datetime.now().date()
        
        # Load previous post count from log
        self.load_daily_post_count()
    
    def load_daily_post_count(self):
        """Load the daily post count from the log file"""
        log_file = self.logs_dir / "linkedin_posts.json"
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                    today = datetime.now().date()
                    self.daily_post_count = sum(1 for log in logs if datetime.fromisoformat(log['timestamp']).date() == today)
            except Exception as e:
                logger.warning(f"Could not load post count from log: {e}")
    
    async def initialize_browser(self):
        """Initialize the browser with saved session data"""
        logger.info("Initializing LinkedIn browser with session persistence...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_dir),
            headless=False,  # Set to True if you don't want to see the browser
            viewport={'width': 1280, 'height': 800},
            args=[
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Navigate to LinkedIn
        self.page = await self.browser.new_page()
        await self.page.goto('https://www.linkedin.com/feed/')
        
        # Wait for LinkedIn to load
        try:
            # Check if already logged in by looking for the feed
            await self.page.wait_for_selector('main-content', timeout=10000)
            logger.info("LinkedIn loaded successfully with existing session!")
        except Exception as e:
            logger.warning(f"Not logged in. Attempting to log in... Error: {e}")
            # Proceed to login
            await self.login()
    
    async def login(self):
        """Login to LinkedIn"""
        email = os.getenv('LINKEDIN_EMAIL')
        password = os.getenv('LINKEDIN_PASSWORD')
        
        if not email or not password:
            raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env file")
        
        # Navigate to login page
        await self.page.goto('https://www.linkedin.com/login')
        
        # Fill in login credentials
        await self.page.fill('input#username', email)
        await self.page.fill('input#password', password)
        
        # Click login button
        await self.page.click('button[type="submit"]')
        
        # Wait for possible 2FA or redirect to feed
        try:
            # Wait for feed to load (indicates successful login)
            await self.page.wait_for_selector('main-content', timeout=30000)
            logger.info("Logged in to LinkedIn successfully!")
        except:
            # Check if 2FA is required
            try:
                await self.page.wait_for_selector('input#input__email_verification_pin', timeout=10000)
                logger.info("2FA required. Please enter the code manually.")
                await self.page.wait_for_selector('main-content', timeout=60000)  # Wait for user to enter 2FA
            except:
                logger.error("Login failed. Please check credentials.")
                raise
    
    async def check_notifications(self):
        """Check for new notifications (connection requests, messages, job opportunities)"""
        logger.info("Checking LinkedIn notifications...")
        
        try:
            # Navigate to notifications page
            await self.page.goto('https://www.linkedin.com/notifications/')
            
            # Wait for notifications to load
            await self.page.wait_for_selector('.notification-card', timeout=10000)
            
            # Find notification cards
            notification_cards = await self.page.query_selector_all('.notification-card')
            
            for card in notification_cards:
                # Extract notification details
                title_element = await card.query_selector('.notification-card__title')
                subtitle_element = await card.query_selector('.notification-card__subtitle')
                
                if title_element:
                    title = await title_element.text_content()
                    subtitle = ""
                    if subtitle_element:
                        subtitle = await subtitle_element.text_content()
                    
                    # Determine notification type
                    notification_type = None
                    if "connection" in title.lower() or "connection" in subtitle.lower():
                        notification_type = "connection_request"
                    elif "message" in title.lower() or "message" in subtitle.lower():
                        notification_type = "message"
                    elif "job" in title.lower() or "opportunity" in title.lower():
                        notification_type = "opportunity"
                    
                    if notification_type:
                        await self.create_notification_file(notification_type, title, subtitle)
                        
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
    
    async def create_notification_file(self, notification_type, title, subtitle):
        """Create a markdown file in Needs_Action/ for each notification"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"LINKEDIN_{notification_type.upper()}_{timestamp}.md"
        filepath = self.needs_action_dir / filename
        
        # Format the received timestamp
        received_time = datetime.now().isoformat()
        
        # Create the markdown content
        content = f"""---
type: linkedin_{notification_type}
title: {title}
subtitle: {subtitle}
received: {received_time}
priority: medium
status: pending
---

## Notification Details
{title}

### Action Required
- [ ] Review notification
- [ ] Respond appropriately
- [ ] Update status
"""
        
        # Write the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Created notification file: {filepath}")
    
    async def check_new_connections(self):
        """Check for new connection requests"""
        logger.info("Checking for new connection requests...")
        
        try:
            # Navigate to My Network page
            await self.page.goto('https://www.linkedin.com/mynetwork/')
            
            # Look for pending connection requests
            connection_requests = await self.page.query_selector_all('li:has(.invitation-card__container)')
            
            for request in connection_requests:
                # Extract sender info
                name_element = await request.query_selector('.invitation-card__title')
                if name_element:
                    name = await name_element.text_content()
                    
                    # Create notification file
                    await self.create_notification_file(
                        "connection_request",
                        f"New connection request from {name}",
                        f"{name} wants to connect with you"
                    )
        
        except Exception as e:
            logger.error(f"Error checking connection requests: {e}")
    
    async def check_messages(self):
        """Check for new messages"""
        logger.info("Checking for new messages...")
        
        try:
            # Navigate to Messages page
            await self.page.goto('https://www.linkedin.com/messaging/')
            
            # Wait for messages to load
            await self.page.wait_for_selector('.msg-thread', timeout=10000)
            
            # Find unread message threads
            unread_threads = await self.page.query_selector_all('.msg-thread--unread')
            
            for thread in unread_threads:
                # Extract thread info
                title_element = await thread.query_selector('.msg-thread__thread-title')
                if title_element:
                    title = await title_element.text_content()
                    
                    # Create notification file
                    await self.create_notification_file(
                        "message",
                        f"New message from {title}",
                        f"You have a new message from {title}"
                    )
        
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
    
    async def start_watching(self, interval=7200):  # Default to 2 hours (7200 seconds)
        """Start watching for LinkedIn notifications"""
        logger.info("Starting LinkedIn monitoring...")
        logger.info(f"Checking every {interval} seconds...")
        
        try:
            await self.initialize_browser()
            
            while True:
                await self.check_notifications()
                await self.check_new_connections()
                await self.check_messages()
                
                logger.info(f"Waiting {interval} seconds until next check...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("LinkedIn monitoring stopped by user.")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            if self.browser:
                await self.browser.close()
    
    async def post_approved_content(self):
        """Post approved content to LinkedIn"""
        logger.info("Checking for approved content to post...")
        
        # Check if we've reached the daily limit
        if self.daily_post_count >= 3:
            logger.info("Daily post limit reached (3 posts per day)")
            return
        
        # Reset daily counter if it's a new day
        today = datetime.now().date()
        if today != self.post_reset_date:
            self.daily_post_count = 0
            self.post_reset_date = today
        
        # Look for approved posts
        approved_posts = list(self.approved_dir.glob("LINKEDIN_POST_*.md"))
        
        for post_file in approved_posts:
            try:
                # Read the post content
                with open(post_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the frontmatter and content
                lines = content.split('\n')
                frontmatter_start = -1
                frontmatter_end = -1
                
                for i, line in enumerate(lines):
                    if line.strip() == '---':
                        if frontmatter_start == -1:
                            frontmatter_start = i
                        elif frontmatter_end == -1:
                            frontmatter_end = i
                            break
                
                if frontmatter_start != -1 and frontmatter_end != -1:
                    frontmatter_str = '\n'.join(lines[frontmatter_start+1:frontmatter_end])
                    post_body = '\n'.join(lines[frontmatter_end+1:])
                    
                    # Parse frontmatter as YAML-like structure
                    frontmatter = {}
                    current_key = None
                    current_value = []
                    
                    for line in frontmatter_str.split('\n'):
                        if ':' in line and not line.startswith('  ') and not line.startswith('    '):
                            if current_key is not None:
                                # Save the previous key-value pair
                                if len(current_value) == 1:
                                    frontmatter[current_key] = current_value[0].strip()
                                else:
                                    frontmatter[current_key] = '\n'.join(current_value).strip()
                            
                            parts = line.split(':', 1)
                            current_key = parts[0].strip()
                            current_value = [parts[1].strip()] if len(parts) > 1 else []
                        else:
                            if current_key:
                                current_value.append(line)
                    
                    # Save the last key-value pair
                    if current_key is not None:
                        if len(current_value) == 1:
                            frontmatter[current_key] = current_value[0].strip()
                        else:
                            frontmatter[current_key] = '\n'.join(current_value).strip()
                    
                    # Check if this post should be scheduled for later
                    scheduled_time = frontmatter.get('scheduled_time', 'immediate')
                    if scheduled_time != 'immediate':
                        try:
                            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                            if datetime.now() < scheduled_datetime:
                                logger.info(f"Post {post_file.name} is scheduled for later: {scheduled_time}")
                                continue  # Skip this post for now
                        except ValueError:
                            logger.warning(f"Invalid scheduled time format in {post_file.name}: {scheduled_time}")
                    
                    # Post the content
                    success = await self.make_post(frontmatter, post_body)
                    
                    if success:
                        # Update daily post count
                        self.daily_post_count += 1
                        
                        # Log the post
                        self.log_post(frontmatter.get('title', 'Untitled'), post_file.name)
                        
                        # Move the file to Posted/ folder (create if doesn't exist)
                        posted_dir = Path("Posted")
                        posted_dir.mkdir(exist_ok=True)
                        new_path = posted_dir / post_file.name
                        post_file.rename(new_path)
                        
                        logger.info(f"Successfully posted content from {post_file.name}")
                    else:
                        logger.error(f"Failed to post content from {post_file.name}")
                
            except Exception as e:
                logger.error(f"Error processing approved post {post_file.name}: {e}")
    
    async def make_post(self, frontmatter, post_body):
        """Actually make the post to LinkedIn"""
        try:
            # Navigate to the post creation page
            await self.page.goto('https://www.linkedin.com/feed/')
            
            # Wait for the post textbox to appear
            await self.page.wait_for_selector('div[contenteditable="true"][data-test-id="artdeco-text-input-content-editable"]', timeout=10000)
            
            # Click on the post textbox to activate it
            await self.page.click('div[contenteditable="true"][data-test-id="artdeco-text-input-content-editable"]')
            
            # Type the post content
            await self.page.keyboard.type(post_body)
            
            # Add hashtags if provided
            hashtags = frontmatter.get('hashtags', [])
            if hashtags and isinstance(hashtags, list):
                hashtag_str = ' '.join([f"#{tag}" for tag in hashtags])
                await self.page.keyboard.type(f"\n\n{hashtag_str}")
            
            # Add image if provided
            image_path = frontmatter.get('image_path')
            if image_path:
                # Click the media upload button
                await self.page.click('button[aria-label="Add a photo/video"]')
                
                # Wait for file input to appear and upload the image
                await self.page.wait_for_selector('input[type="file"]', timeout=5000)
                file_input = await self.page.query_selector('input[type="file"]')
                await file_input.set_input_files(image_path)
            
            # Click the post button
            await self.page.click('button[aria-label="Post"]')
            
            # Wait a bit to ensure post was successful
            await self.page.wait_for_timeout(3000)
            
            logger.info("Successfully made LinkedIn post")
            return True
            
        except Exception as e:
            logger.error(f"Error making LinkedIn post: {e}")
            return False
    
    def log_post(self, title, filename):
        """Log the post to the analytics file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'filename': str(filename),
            'post_number': self.daily_post_count
        }
        
        log_file = self.logs_dir / "linkedin_posts.json"
        logs = []
        
        # Load existing logs if file exists
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        # Append new log entry
        logs.append(log_entry)
        
        # Write back to file
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    async def start_posting_monitor(self, interval=300):  # Check every 5 minutes
        """Start monitoring for approved content to post"""
        logger.info("Starting LinkedIn posting monitor...")
        logger.info(f"Checking for approved content every {interval} seconds...")
        
        try:
            await self.initialize_browser()
            
            while True:
                await self.post_approved_content()
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("LinkedIn posting monitor stopped by user.")
        except Exception as e:
            logger.error(f"Error in posting monitor loop: {e}")
        finally:
            if self.browser:
                await self.browser.close()


async def main():
    """
    Main entry point for LinkedIn integration
    
    This can run both the watcher and poster simultaneously using asyncio tasks
    """
    linkedin = LinkedInIntegration()
    
    # Run both functions concurrently
    await asyncio.gather(
        linkedin.start_watching(interval=7200),  # Watch every 2 hours
        linkedin.start_posting_monitor(interval=300)  # Check for posts every 5 minutes
    )


if __name__ == "__main__":
    asyncio.run(main())