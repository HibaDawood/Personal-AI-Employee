# 🥈 Silver Tier Documentation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SILVER TIER AI EMPLOYEE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │   WATCHERS  │    │  ORCHESTRATOR│    │   MCP SERVERS        │   │
│  │             │    │              │    │                      │   │
│  │ • Gmail     │◄──►│ • Task       │◄──►│ • Email              │   │
│  │ • WhatsApp  │    │   Detection  │    │ • LinkedIn (future)  │   │
│  │ • LinkedIn  │    │ • Planning   │    │ • Browser (future)   │   │
│  │ • File Sys  │    │ • Execution  │    │                      │   │
│  └─────────────┘    └──────────────┘    └──────────────────────┘   │
│         │                     │                           │         │
│         ▼                     ▼                           ▼         │
│  ┌─────────────┐    ┌─────────────────┐          ┌──────────────┐  │
│  │NEEDS_ACTION │    │   APPROVAL      │          │   SCHEDULER  │  │
│  │    FOLDER   │    │   WORKFLOW      │          │              │  │
│  │             │    │                 │          │ • Health     │  │
│  └─────────────┘    │ • Pending       │          │   Checks     │  │
│                     │ • Approved      │          │ • Summaries  │  │
│                     │ • Rejected      │          │ • Reviews    │  │
│                     │ • Expiry        │          └──────────────┘  │
│                     └─────────────────┘                  │         │
│                              │                           ▼         │
│                              ▼                    ┌──────────────┐ │
│                       ┌─────────────┐            │   DASHBOARD  │ │
│                       │    DONE     │            │              │ │
│                       │   FOLDER    │            │ • Stats      │ │
│                       └─────────────┘            │ • Status     │ │
│                                                  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Watchers (3+)

#### Gmail Watcher (`gmail_watcher.py`)
- **Frequency**: Every 2 minutes
- **Function**: Monitors Gmail inbox for new emails
- **Features**:
  - OAuth2 authentication
  - Keyword detection ('urgent', 'asap', 'help', etc.)
  - Creates action items in Needs_Action/
  - Detailed logging to Logs/gmail_watcher.log

#### WhatsApp Watcher (`whatsapp_watcher.py`)
- **Frequency**: Every 30 seconds
- **Function**: Monitors WhatsApp Web for messages
- **Features**:
  - Playwright-based browser automation
  - Session persistence to avoid QR scanning
  - Keyword monitoring ('urgent', 'asap', 'invoice', 'payment', 'help', 'pricing')
  - Creates action items in Needs_Action/
  - Detailed logging to Logs/whatsapp_watcher.log

#### LinkedIn Watcher (`linkedin_integration.py`)
- **Frequency**: Every 2 hours
- **Function**: Monitors LinkedIn for connections/messages/opportunities
- **Features**:
  - Playwright-based browser automation
  - Session persistence
  - Monitors: new connections, messages, job opportunities
  - Creates action items in Needs_Action/
  - Auto-posting with approval workflow
  - Detailed logging to Logs/linkedin_integration.log

#### File System Watcher (`filesystem_watcher.py`)
- **Frequency**: Continuous monitoring
- **Function**: Watches Drop_Zone/ folder for new files
- **Features**:
  - Real-time file change detection
  - Creates action items in Needs_Action/
  - Detailed logging to Logs/filesystem_watcher.log

### 2. Orchestrator + Planning (`orchestrator.py`)

#### Task Detection
- Monitors Needs_Action/ folder for new tasks
- Priority queuing based on urgency keywords
- Concurrent task processing (up to 3 tasks)

#### Plan Creation via Claude
- Creates structured Plan.md files in Plans/ folder
- Includes objective, steps, resources needed
- Determines approval requirements automatically

#### Step-by-Step Execution
- Follows plan checklist items
- Updates progress in real-time
- Handles approval workflow integration

#### Multi-Task Handling
- Processes up to 3 tasks simultaneously
- Prevents conflicts between similar tasks
- Maintains task isolation

### 3. MCP Servers

#### Email MCP Server (`email_mcp_server.js`)
- **Protocol**: Model Context Protocol compliant
- **Functions**:
  - `send_email`: Sends emails via Gmail SMTP
  - `draft_email`: Creates draft emails for approval
  - `search_sent_emails`: Searches historical emails
- **Features**:
  - Gmail App Password authentication
  - HTML email support
  - Attachment handling
  - Rate limiting (50 emails/day)
  - Approval integration

### 4. Approval Workflow (`approval_manager.py`)

#### Pending → Approved/Rejected
- Monitors Pending_Approval/ folder
- Executes actions when moved to Approved/
- Logs rejections when moved to Rejected/

#### Expiry Handling
- Auto-rejects requests after 24 hours
- Updates files with expiry information
- Moves expired requests to Rejected/

#### Analytics Tracking
- Tracks approval rates and response times
- Monitors rejection patterns
- Updates Company_Handbook.md with learnings

### 5. Scheduler (`scheduler.py`)

#### Automated Health Checks
- Every 30 minutes: Verifies all watchers are running
- Restarts crashed processes automatically
- Updates Dashboard with system status

#### Daily Summaries
- 8 AM: Morning briefing with yesterday's summary
- 6 PM: End-of-day summary with today's accomplishments

#### Weekly Reviews
- Sunday 8 PM: Weekly business review
- Performance metrics and trend analysis

## Setup Instructions

### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for MCP server)
npm install
```

### Component Setup

#### 1. Gmail Watcher Setup
1. Enable Gmail API and create credentials
2. Download `credentials.json` and `token.json` to project root
3. Add Gmail credentials to `.env`:
   ```
   GMAIL_USER=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_app_password
   ```

#### 2. WhatsApp Watcher Setup
1. Install Playwright: `pip install playwright`
2. Install browsers: `playwright install chromium`
3. Run once to scan QR code: `python whatsapp_watcher.py`
4. Session will be saved automatically

#### 3. LinkedIn Integration Setup
1. Install Playwright: `pip install playwright`
2. Install browsers: `playwright install chromium`
3. Add LinkedIn credentials to `.env`:
   ```
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   ```
4. Run once to login and save session: `python linkedin_integration.py`

#### 4. Email MCP Server Setup
1. Install Node.js dependencies: `npm install`
2. Configure Gmail credentials in `.env` (see above)
3. Start MCP server: `node email_mcp_server.js`

#### 5. Scheduler Setup
1. Install Python dependencies: `pip install schedule psutil`
2. Start scheduler: `python scheduler.py`
3. For system startup, use platform-specific setup (see SCHEDULING_SETUP.md)

## Configuration

### .env Variables Explained
```
# Gmail Configuration
GMAIL_USER=your_gmail_address@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password

# LinkedIn Configuration
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password

# Claude API (if applicable)
CLAUDE_API_KEY=your_claude_api_key
```

### Company_Handbook.md Rules
- Contains trusted contacts list
- Defines company policies and procedures
- Specifies approval requirements for different actions
- Includes tone and communication guidelines

### Trusted Contacts List
- Located in Company_Handbook.md under "Trusted Contacts" section
- Emails in this list bypass approval for sensitive actions
- Format: One email per line or bulleted list

## Usage Examples

### Example 1: Processing an Urgent Email
1. Gmail watcher detects email with "URGENT" in subject
2. Creates `EMAIL_john_doe_20260212_143000.md` in Needs_Action/
3. Orchestrator detects new task and creates Plan.md
4. Plan identifies need for approval due to urgency
5. Creates approval request in Pending_Approval/
6. Human approves by moving to Approved/ folder
7. Email MCP server sends response
8. Task moved to Done/ folder
9. Dashboard updated with completion

### Example 2: WhatsApp Message with Invoice Request
1. WhatsApp watcher detects message containing "invoice"
2. Creates `WHATSAPP_Jane_Smith_20260212_154500.md` in Needs_Action/
3. Orchestrator creates plan with steps
4. Plan identifies financial action requiring approval
5. Creates draft invoice in Pending_Approval/
6. Human reviews and approves
7. Invoice sent via email MCP
8. Task completed and logged

### Example 3: LinkedIn Connection Request
1. LinkedIn watcher detects new connection request
2. Creates `LINKEDIN_CONNECTION_REQUEST_20260212_160000.md` in Needs_Action/
3. Orchestrator evaluates and determines appropriate response
4. Creates response draft for approval
5. Human approves and response is sent
6. Connection accepted automatically
7. Task completed

## Troubleshooting

### Common Errors and Fixes

#### Gmail Authentication Issues
```
Problem: "Invalid credentials" error
Solution:
1. Verify GMAIL_USER and GMAIL_APP_PASSWORD in .env
2. Regenerate Gmail App Password if needed
3. Ensure 2FA is enabled on Google account
```

#### WhatsApp Session Problems
```
Problem: QR code keeps appearing
Solution:
1. Check whatsapp_session/ folder permissions
2. Verify Playwright installation: `playwright install chromium`
3. Manually run WhatsApp watcher once to establish session
```

#### LinkedIn Login Failures
```
Problem: Cannot login to LinkedIn
Solution:
1. Verify LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env
2. Check for CAPTCHA challenges
3. Clear linkedin_session/ folder and retry login
```

#### MCP Server Connection Issues
```
Problem: Claude cannot connect to MCP server
Solution:
1. Verify email_mcp_server.js is running
2. Check email_mcp_config.json path configuration
3. Ensure Node.js and required packages are installed
```

### Debug Mode Instructions
```bash
# Run orchestrator in debug mode
python orchestrator.py --debug

# Run watchers individually for debugging
python gmail_watcher.py
python whatsapp_watcher.py
python linkedin_integration.py

# Run scheduler in verbose mode
python scheduler.py --verbose

# Run approval manager in debug mode
python approval_manager.py --verbose
```

### Log File Locations
- `Logs/orchestrator.log` - Orchestrator activities
- `Logs/gmail_watcher.log` - Gmail watcher logs
- `Logs/whatsapp_watcher.log` - WhatsApp watcher logs
- `Logs/linkedin_integration.log` - LinkedIn integration logs
- `Logs/email_mcp_server.log` - Email MCP server logs
- `Logs/scheduler.log` - Scheduler activities
- `Logs/approval_manager.log` - Approval workflow logs
- `Logs/sent_emails.json` - Record of sent emails
- `Logs/approval_stats.json` - Approval analytics
- `Logs/test_results.json` - Test execution results

### Troubleshooting Flowchart

```
Issue Detected
      │
      ▼
Is it a Watcher Issue?
      │
      ├─ YES ──► Check Watcher Logs ──► Restart Watcher ──► Monitor
      │
      └─ NO ───► Is it MCP Related?
                    │
                    ├─ YES ──► Check MCP Server ──► Restart MCP ──► Verify Connection
                    │
                    └─ NO ───► Is it Orchestrator?
                                  │
                                  ├─ YES ──► Check Orchestrator Log ──► Restart Orchestrator
                                  │
                                  └─ NO ───► Check Scheduler ──► Check Approval Manager
```

## Silver Tier Checklist

- [x] All Bronze items ✓
- [x] 2+ watchers running (Gmail, WhatsApp, LinkedIn, File System)
- [x] LinkedIn auto-posting works
- [x] Claude creates Plan.md files
- [x] Email MCP server functional
- [x] Approval workflow tested
- [x] Scheduling configured
- [x] Agent Skills implemented
- [x] All tests passing (run: `python test_silver_tier.py`)

## Performance Metrics

### Tasks Processed Per Day
- **Target**: 50-100 tasks per day
- **Measurement**: Count in Done/ folder daily
- **Tracking**: Dashboard.md "Completed Today" metric

### Approval Response Time
- **Target**: < 4 hours for standard requests
- **Measurement**: Time between request creation and approval/rejection
- **Tracking**: Logs/approval_stats.json

### Error Rate
- **Target**: < 5% error rate
- **Measurement**: Failed tasks / Total tasks processed
- **Tracking**: Error logs in respective component logs

### Uptime Percentage
- **Target**: > 95% uptime
- **Measurement**: Time system is operational vs. downtime
- **Tracking**: Scheduler health checks and Dashboard status

## Command Reference

### Starting Components
```bash
# Start all watchers
python gmail_watcher.py
python whatsapp_watcher.py
python linkedin_integration.py
python filesystem_watcher.py

# Start orchestrator
python orchestrator.py

# Start approval manager
python approval_manager.py

# Start scheduler
python scheduler.py

# Start email MCP server
node email_mcp_server.js
```

### Testing Commands
```bash
# Run comprehensive tests
python test_silver_tier.py --verbose

# Run specific component tests
python test_silver_tier.py --clean  # Clean up test data after running
```

### Utility Commands
```bash
# Check system status
python orchestrator.py --health-check

# Update dashboard manually
python orchestrator.py --update-dashboard

# Create sample approval request
python approval_manager.py create_sample email_send "Test email content" high
```

### Log Management
```bash
# View orchestrator logs
tail -f Logs/orchestrator.log

# View all watcher logs
tail -f Logs/*.log

# Clean old logs (keeping last 7 days)
find Logs/ -name "*.log" -mtime +7 -delete
```

### Configuration Management
```bash
# Verify environment variables
python -c "import os; print(os.getenv('GMAIL_USER'))"

# Check if all required directories exist
ls -la Needs_Action/ Pending_Approval/ Approved/ Rejected/ Done/ Plans/
```