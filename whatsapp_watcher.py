"""
WhatsApp Web Watcher for Silver Tier AI Employee

Monitors WhatsApp Web for messages containing specific keywords and creates
action items in the Needs_Action folder.

Setup Instructions:
1. First run: The browser will open and you'll need to scan the QR code with your phone
2. Subsequent runs: The session will be restored from whatsapp_session/ folder
3. Session persistence: Login credentials are saved to avoid re-scanning QR code

WARNING: Using automation tools with WhatsApp may violate WhatsApp's Terms of Service.
Use this script responsibly and at your own risk.

Dependencies:
- Playwright: pip install playwright
- Also run: playwright install chromium

Required keywords to monitor: 'urgent', 'asap', 'invoice', 'payment', 'help', 'pricing'
"""

import asyncio
import json
import os
import re
import logging
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/whatsapp_watcher.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class WhatsAppWatcher:
    def __init__(self):
        self.session_dir = Path("whatsapp_session")
        self.needs_action_dir = Path("Needs_Action")
        self.logs_dir = Path("Logs")
        self.browser = None
        self.page = None
        
        # Keywords to monitor
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'pricing']
        
        # Create directories if they don't exist
        self.session_dir.mkdir(exist_ok=True)
        self.needs_action_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    async def initialize_browser(self):
        """Initialize the browser with saved session data"""
        logger.info("Initializing browser with session persistence...")
        
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
        
        # Navigate to WhatsApp Web
        self.page = await self.browser.new_page()
        await self.page.goto('https://web.whatsapp.com/')
        
        # Wait for WhatsApp to load
        try:
            # Wait for the main app to load (this indicates successful login or QR scan)
            await self.page.wait_for_selector('div[data-testid="chat-list"]', timeout=30000)
            logger.info("WhatsApp Web loaded successfully with existing session!")
        except Exception as e:
            logger.warning(f"Session not found or expired. Waiting for QR code scan... Error: {e}")
            # Wait for user to scan QR code
            await self.page.wait_for_selector('div[data-testid="chat-list"]', timeout=60000)
            logger.info("QR code scanned successfully. Session saved for future use.")
    
    async def check_unread_messages(self):
        """Check for unread messages containing monitored keywords"""
        try:
            logger.info("Checking for unread messages with monitored keywords...")
            
            # Find all unread chats
            unread_chats = await self.page.query_selector_all(
                'div[data-testid="conversation"] div[data-testid="unread-count"]'
            )
            
            matching_messages = []
            
            for chat in unread_chats:
                # Click on the chat to open it
                chat_container = await chat.evaluate_handle('node => node.parentElement.parentElement.parentElement')
                await chat_container.click()
                
                # Wait for messages to load
                await self.page.wait_for_timeout(2000)
                
                # Get contact name
                contact_selector = 'header span[dir="auto"]'
                try:
                    contact_element = await self.page.wait_for_selector(contact_selector, timeout=5000)
                    contact_name = await contact_element.text_content()
                except:
                    logger.warning("Could not get contact name, using 'Unknown'")
                    contact_name = "Unknown"
                
                # Get all message bubbles (both incoming and outgoing)
                message_bubbles = await self.page.query_selector_all(
                    'div.message-in span.selectable-text, div.message-out span.selectable-text'
                )
                
                for msg_bubble in message_bubbles:
                    message_text = await msg_bubble.text_content()
                    
                    # Check for keywords in the message
                    matched_keywords = []
                    for keyword in self.keywords:
                        if re.search(r'\b' + re.escape(keyword) + r'\b', message_text.lower(), re.IGNORECASE):
                            matched_keywords.append(keyword)
                    
                    if matched_keywords:
                        matching_messages.append({
                            'contact_name': contact_name,
                            'message_text': message_text.strip(),
                            'matched_keywords': matched_keywords
                        })
                        logger.info(f"Found matching message from {contact_name} with keywords: {matched_keywords}")
            
            logger.info(f"Found {len(matching_messages)} messages with monitored keywords")
            return matching_messages
            
        except Exception as e:
            logger.error(f"Error checking unread messages: {e}")
            return []
    
    async def create_action_item(self, message_data):
        """Create a markdown file in Needs_Action/ for each matching message"""
        try:
            # Sanitize contact name for filename
            contact_name = re.sub(r'[<>:"/\\|?*]', '_', message_data['contact_name'])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"WHATSAPP_{contact_name}_{timestamp}.md"
            filepath = self.needs_action_dir / filename
            
            # Truncate message preview to first 100 characters
            message_preview = message_data['message_text'][:100] if len(message_data['message_text']) > 100 else message_data['message_text']
            
            # Format the received timestamp
            received_time = datetime.now().isoformat()
            
            # Determine priority based on keywords
            high_priority_keywords = ['urgent', 'asap', 'payment']
            priority = 'high' if any(kw in message_data['matched_keywords'] for kw in high_priority_keywords) else 'medium'
            
            # Create the markdown content
            content = f"""---
type: whatsapp
from: {message_data['contact_name']}
message_preview: {message_preview}
keywords_matched: {message_data['matched_keywords']}
received: {received_time}
priority: {priority}
status: pending
---

## Message Content
{message_data['message_text']}

## Suggested Actions
- [ ] Draft reply
- [ ] Create invoice (if invoice/payment mentioned)
- [ ] Escalate to human
"""
            
            # Write the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Created action item: {filepath}")
            
        except Exception as e:
            logger.error(f"Error creating action item: {e}")
    
    async def run_monitoring_cycle(self):
        """Run one cycle of monitoring for keyword-containing messages"""
        logger.info("Starting monitoring cycle...")
        
        try:
            matching_messages = await self.check_unread_messages()
            
            for message in matching_messages:
                await self.create_action_item(message)
            
            if matching_messages:
                logger.info(f"Found and processed {len(matching_messages)} messages with keywords!")
            else:
                logger.info("No messages with monitored keywords found.")
                
        except Exception as e:
            logger.error(f"Error during monitoring cycle: {e}")
    
    async def start_monitoring(self, interval=30):
        """Start continuous monitoring"""
        logger.info("Starting WhatsApp monitoring...")
        logger.info(f"Monitoring for keywords: {', '.join(self.keywords)}")
        logger.info(f"Checking every {interval} seconds...")
        
        try:
            await self.initialize_browser()
            
            while True:
                await self.run_monitoring_cycle()
                logger.info(f"Waiting {interval} seconds until next check...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user.")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            if self.browser:
                await self.browser.close()


async def main():
    """
    Main entry point for the WhatsApp watcher
    
    Setup Guide:
    1. On first run, scan the QR code that appears in the browser window
    2. The session will be saved automatically to whatsapp_session/ folder
    3. On subsequent runs, the saved session will be used automatically
    4. The script will monitor for messages containing the specified keywords
    5. Matching messages will be saved to the Needs_Action/ folder
    
    WARNING: This script automates interaction with WhatsApp Web. Please review
    WhatsApp's Terms of Service before using this script. Use at your own risk.
    """
    watcher = WhatsAppWatcher()
    await watcher.start_monitoring(interval=30)


if __name__ == "__main__":
    asyncio.run(main())