/**
 * Email MCP Server for Silver Tier AI Employee
 * 
 * Implements Model Context Protocol for email operations
 * 
 * SETUP INSTRUCTIONS:
 * 1. Enable 2-factor authentication on your Google account
 * 2. Generate an App Password: Google Account > Security > App passwords
 * 3. Add to .env file:
 *    GMAIL_USER=your_email@gmail.com
 *    GMAIL_APP_PASSWORD=your_app_password_here
 * 
 * MCP PROTOCOL IMPLEMENTATION:
 * - Handles MCP handshake and capability discovery
 * - Implements send_email, draft_email, and search_sent_emails tools
 * - Follows MCP JSON-RPC 2.0 specification
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const nodemailer = require('nodemailer');
require('dotenv').config();

// Configuration
const MAX_DAILY_EMAILS = 50;
const LOGS_DIR = './Logs';
const PENDING_APPROVAL_DIR = './Pending_Approval';
const SENT_EMAILS_LOG = path.join(LOGS_DIR, 'sent_emails.json');

// Ensure directories exist
if (!fs.existsSync(LOGS_DIR)) {
    fs.mkdirSync(LOGS_DIR, { recursive: true });
}
if (!fs.existsSync(PENDING_APPROVAL_DIR)) {
    fs.mkdirSync(PENDING_APPROVAL_DIR, { recursive: true });
}

// Daily email counter
let dailyEmailCount = 0;
let today = new Date().toISOString().split('T')[0];

// Initialize sent emails log
function initSentEmailsLog() {
    if (!fs.existsSync(SENT_EMAILS_LOG)) {
        fs.writeFileSync(SENT_EMAILS_LOG, JSON.stringify([]));
    }
}

// Load sent emails log
function loadSentEmails() {
    try {
        const data = fs.readFileSync(SENT_EMAILS_LOG, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Error loading sent emails log:', error);
        return [];
    }
}

// Save sent emails log
function saveSentEmails(emails) {
    fs.writeFileSync(SENT_EMAILS_LOG, JSON.stringify(emails, null, 2));
}

// Check if we've reached the daily limit
function checkDailyLimit() {
    const todayStr = new Date().toISOString().split('T')[0];
    
    // Reset counter if it's a new day
    if (today !== todayStr) {
        today = todayStr;
        dailyEmailCount = 0;
    }
    
    // Count emails sent today
    const sentEmails = loadSentEmails();
    dailyEmailCount = sentEmails.filter(email => email.date.startsWith(todayStr)).length;
    
    return dailyEmailCount < MAX_DAILY_EMAILS;
}

// Get trusted contacts from Company_Handbook.md
function getTrustedContacts() {
    try {
        const handbookPath = './Company_Handbook.md';
        if (!fs.existsSync(handbookPath)) {
            console.warn('Company_Handbook.md not found, assuming no trusted contacts');
            return [];
        }
        
        const content = fs.readFileSync(handbookPath, 'utf8');
        const lines = content.split('\n');
        const trustedContacts = [];
        
        // Look for a "Trusted Contacts" section
        let inTrustedSection = false;
        for (const line of lines) {
            if (line.toLowerCase().includes('trusted contacts')) {
                inTrustedSection = true;
                continue;
            }
            
            if (inTrustedSection) {
                // Stop when we reach the next section
                if (line.trim().startsWith('#')) {
                    break;
                }
                
                // Look for email addresses in the line
                const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
                const matches = line.match(emailRegex);
                if (matches) {
                    trustedContacts.push(...matches);
                }
            }
        }
        
        return trustedContacts.map(email => email.toLowerCase());
    } catch (error) {
        console.error('Error reading Company_Handbook.md:', error);
        return [];
    }
}

// Check if recipient is trusted
function isTrustedContact(recipient) {
    const trustedContacts = getTrustedContacts();
    return trustedContacts.includes(recipient.toLowerCase());
}

// Create approval file for new contacts
function createApprovalFile(to, subject, body) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `EMAIL_APPROVAL_${timestamp}.md`;
    const filepath = path.join(PENDING_APPROVAL_DIR, filename);
    
    const content = `---
type: email_approval
to: ${to}
subject: ${subject}
request_date: ${new Date().toISOString()}
status: pending_review
---

## Email Content
**To:** ${to}
**Subject:** ${subject}

${body}

## Approval Options
- Move this file to Approved/ folder to send the email
- Move this file to Rejected/ folder to discard
`;
    
    fs.writeFileSync(filepath, content);
    console.log(`Created approval file: ${filepath}`);
}

// Create nodemailer transporter
function createTransporter() {
    return nodemailer.createTransporter({
        host: 'smtp.gmail.com',
        port: 587,
        secure: false, // true for 465, false for other ports
        auth: {
            user: process.env.GMAIL_USER,
            pass: process.env.GMAIL_APP_PASSWORD
        }
    });
}

// Send email function
async function sendEmail({ to, subject, body, attachments = [] }) {
    try {
        // Check daily limit
        if (!checkDailyLimit()) {
            return {
                success: false,
                error: `Daily email limit (${MAX_DAILY_EMAILS}) reached`
            };
        }
        
        // Check if recipient is trusted
        if (!isTrustedContact(to)) {
            // Create approval file for new contact
            createApprovalFile(to, subject, body);
            return {
                success: false,
                message: `Recipient not trusted. Approval required. Created approval file.`,
                requires_approval: true
            };
        }
        
        // Create transporter
        const transporter = createTransporter();
        
        // Prepare attachments
        const attachmentList = attachments.map(filePath => ({
            filename: path.basename(filePath),
            path: filePath
        }));
        
        // Send mail
        const info = await transporter.sendMail({
            from: process.env.GMAIL_USER,
            to,
            subject,
            html: body, // Treat as HTML
            attachments: attachmentList
        });
        
        // Log sent email
        const sentEmails = loadSentEmails();
        sentEmails.push({
            message_id: info.messageId,
            to,
            subject,
            date: new Date().toISOString(),
            success: true
        });
        saveSentEmails(sentEmails);
        
        // Increment daily count
        dailyEmailCount++;
        
        return {
            success: true,
            message_id: info.messageId
        };
    } catch (error) {
        console.error('Error sending email:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Draft email function
function draftEmail({ to, subject, body }) {
    try {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `EMAIL_DRAFT_${timestamp}.md`;
        const filepath = path.join(PENDING_APPROVAL_DIR, filename);
        
        const content = `---
type: email_draft
to: ${to}
subject: ${subject}
draft_date: ${new Date().toISOString()}
status: pending_approval
---

## Draft Email Content
**To:** ${to}
**Subject:** ${subject}

${body}

## Approval Options
- Move this file to Approved/ folder to send the email
- Move this file to Rejected/ folder to discard
`;
        
        fs.writeFileSync(filepath, content);
        
        return {
            success: true,
            message: `Draft created: ${filepath}`
        };
    } catch (error) {
        console.error('Error creating draft:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Search sent emails function
function searchSentEmails({ query, max_results = 10 }) {
    try {
        const sentEmails = loadSentEmails();
        
        // Filter emails based on query
        let filteredEmails = sentEmails;
        if (query) {
            const queryLower = query.toLowerCase();
            filteredEmails = sentEmails.filter(email => 
                email.to.toLowerCase().includes(queryLower) ||
                email.subject.toLowerCase().includes(queryLower)
            );
        }
        
        // Limit results
        const limitedResults = filteredEmails.slice(0, max_results);
        
        return {
            success: true,
            results: limitedResults
        };
    } catch (error) {
        console.error('Error searching sent emails:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// MCP Protocol Handler
class MCPServer {
    constructor() {
        this.tools = {
            send_email: {
                name: 'send_email',
                description: 'Send an email to a recipient',
                inputSchema: {
                    type: 'object',
                    properties: {
                        to: {
                            type: 'string',
                            description: 'Recipient email address'
                        },
                        subject: {
                            type: 'string',
                            description: 'Email subject'
                        },
                        body: {
                            type: 'string',
                            description: 'Email body content (HTML)'
                        },
                        attachments: {
                            type: 'array',
                            items: {
                                type: 'string'
                            },
                            description: 'Array of file paths to attach'
                        }
                    },
                    required: ['to', 'subject', 'body']
                }
            },
            draft_email: {
                name: 'draft_email',
                description: 'Create a draft email for approval',
                inputSchema: {
                    type: 'object',
                    properties: {
                        to: {
                            type: 'string',
                            description: 'Recipient email address'
                        },
                        subject: {
                            type: 'string',
                            description: 'Email subject'
                        },
                        body: {
                            type: 'string',
                            description: 'Email body content (HTML)'
                        }
                    },
                    required: ['to', 'subject', 'body']
                }
            },
            search_sent_emails: {
                name: 'search_sent_emails',
                description: 'Search previously sent emails',
                inputSchema: {
                    type: 'object',
                    properties: {
                        query: {
                            type: 'string',
                            description: 'Search query to match against recipients or subjects'
                        },
                        max_results: {
                            type: 'number',
                            description: 'Maximum number of results to return (default: 10)'
                        }
                    }
                }
            }
        };
        
        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });
        
        initSentEmailsLog();
    }
    
    async start() {
        // Handle MCP handshake
        this.rl.on('line', async (input) => {
            try {
                const message = JSON.parse(input);
                
                if (message.method === 'initialize') {
                    // Respond to initialization
                    const response = {
                        jsonrpc: '2.0',
                        id: message.id,
                        result: {
                            capabilities: {
                                tools: Object.values(this.tools)
                            }
                        }
                    };
                    process.stdout.write(JSON.stringify(response) + '\n');
                } else if (message.method === 'call_tool') {
                    // Handle tool calls
                    const { name, arguments: args } = message.params;
                    let result;
                    
                    switch (name) {
                        case 'send_email':
                            result = await sendEmail(args);
                            break;
                        case 'draft_email':
                            result = draftEmail(args);
                            break;
                        case 'search_sent_emails':
                            result = searchSentEmails(args);
                            break;
                        default:
                            result = {
                                success: false,
                                error: `Unknown tool: ${name}`
                            };
                    }
                    
                    const response = {
                        jsonrpc: '2.0',
                        id: message.id,
                        result
                    };
                    process.stdout.write(JSON.stringify(response) + '\n');
                }
            } catch (error) {
                console.error('Error processing message:', error);
                
                const response = {
                    jsonrpc: '2.0',
                    id: message?.id || null,
                    error: {
                        code: -32603,
                        message: error.message
                    }
                };
                process.stdout.write(JSON.stringify(response) + '\n');
            }
        });
        
        // Keep the process alive
        this.rl.on('close', () => {
            process.exit(0);
        });
    }
}

// Start the server
const server = new MCPServer();
server.start();

console.log('Email MCP Server started. Listening for MCP requests...');