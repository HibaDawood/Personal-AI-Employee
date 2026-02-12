import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import pickle

# Import Gmail API modules
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Define the scopes required for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def setup_logging():
    """Setup logging to both console and file"""
    # Create Logs directory if it doesn't exist
    logs_dir = Path("Logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger('GmailWatcher')
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler
    log_file = logs_dir / f"gmail_watcher_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def authenticate_gmail():
    """Authenticate and return Gmail service object"""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logging.error(f"Failed to refresh credentials: {e}")
                # Delete token.json to force re-authentication
                if os.path.exists('token.json'):
                    os.remove('token.json')
                
        # If no valid token, initiate OAuth flow
        if not creds or not creds.valid:
            if os.path.exists('credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            else:
                raise FileNotFoundError("credentials.json file not found. Please download it from Google Cloud Console.")
    
    return build('gmail', 'v1', credentials=creds)

def load_processed_emails():
    """Load previously processed email IDs from JSON file"""
    try:
        if os.path.exists('processed_emails.json'):
            with open('processed_emails.json', 'r') as f:
                return set(json.load(f))
        else:
            return set()
    except Exception as e:
        logging.error(f"Error loading processed emails: {e}")
        return set()

def save_processed_email(email_id):
    """Save processed email ID to JSON file"""
    processed_emails = load_processed_emails()
    processed_emails.add(email_id)
    
    try:
        with open('processed_emails.json', 'w') as f:
            json.dump(list(processed_emails), f)
    except Exception as e:
        logging.error(f"Error saving processed email: {e}")

def create_action_item(sender, subject, snippet, email_id, timestamp):
    """Create a markdown file in Needs_Action folder for each email"""
    try:
        # Sanitize sender name for filename
        sender_name = "".join(c for c in sender.split()[0] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Create filename with timestamp and sender
        filename = f"EMAIL_{timestamp}_{sender_name}.md"
        filepath = Path("Needs_Action") / filename
        
        # Format the received time
        received_time = datetime.fromtimestamp(timestamp).isoformat()
        
        # Create the content
        content = f"""---
type: email
from: {sender}
subject: {subject}
received: {received_time}
priority: high
status: pending
---

## Email Preview
{snippet}

## Suggested Actions
- [ ] Reply to sender
- [ ] Mark as done
"""
        
        # Write the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.info(f"Created action item: {filepath}")
        
    except Exception as e:
        logging.error(f"Error creating action item for email {email_id}: {e}")

def check_gmail(logger):
    """Check Gmail for unread important emails"""
    try:
        # Authenticate to Gmail
        service = authenticate_gmail()
        
        # Load previously processed emails
        processed_emails = load_processed_emails()
        
        # Query for unread important emails
        # Using 'is:important is:unread' to find important unread emails
        results = service.users().messages().list(
            userId='me',
            q='is:important is:unread',
            maxResults=10  # Limit to 10 emails per check
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            logger.info("No new important unread emails found")
            return
        
        logger.info(f"Found {len(messages)} new important unread emails")
        
        # Process each message
        for message in messages:
            msg_id = message['id']
            
            # Skip if already processed
            if msg_id in processed_emails:
                continue
            
            try:
                # Get the full message
                msg = service.users().messages().get(
                    userId='me',
                    id=msg_id
                ).execute()
                
                # Extract headers
                headers = {header['name']: header['value'] for header in msg['payload'].get('headers', [])}
                
                sender = headers.get('From', 'Unknown Sender')
                subject = headers.get('Subject', 'No Subject')
                snippet = msg.get('snippet', '')
                
                # Get timestamp
                timestamp = int(msg['internalDate']) / 1000  # Convert from ms to seconds
                
                # Create action item
                create_action_item(sender, subject, snippet, msg_id, timestamp)
                
                # Mark as processed
                save_processed_email(msg_id)
                
            except Exception as e:
                logger.error(f"Error processing email {msg_id}: {e}")
                
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
    except Exception as e:
        logger.error(f"Unexpected error checking Gmail: {e}")

def main():
    """Main function to run the Gmail watcher"""
    # Setup logging
    logger = setup_logging()
    
    # Create Needs_Action directory if it doesn't exist
    needs_action_dir = Path("Needs_Action")
    needs_action_dir.mkdir(exist_ok=True)
    
    logger.info("Starting Gmail Watcher...")
    
    try:
        while True:
            logger.info("Checking for new important emails...")
            check_gmail(logger)
            
            # Wait for 120 seconds before next check
            logger.info("Waiting 120 seconds before next check...")
            time.sleep(120)
            
    except KeyboardInterrupt:
        logger.info("Gmail Watcher stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")

if __name__ == "__main__":
    main()