# Email Handler Skill

## When to Use This Skill
Use this skill when processing email-related tasks in the Silver Tier AI Employee system. This includes:
- Reading and interpreting incoming emails
- Drafting responses to emails
- Identifying important emails that require action
- Determining if an email requires human approval before responding
- Organizing email content into structured action items

## Input/Output Format

### Input
The skill expects input in the following format:
```markdown
---
type: email
from: sender@example.com
subject: Email Subject
received: 2026-02-12T14:30:00
priority: low/normal/high
status: pending
---

## Email Content
Actual email content goes here...

## Action Required
- [ ] Review content
- [ ] Respond appropriately
- [ ] Update status
```

### Output
The skill produces output in the following format:
```markdown
---
type: email_response
to: sender@example.com
subject: Re: Original Subject
status: drafted/pending_approval
---

## Response Content
Your drafted response goes here...

## Recommended Actions
- [ ] Send response
- [ ] Schedule follow-up
- [ ] Escalate to human
```

## Best Practices

### 1. Tone and Professionalism
- Always maintain a professional and courteous tone
- Match the formality level of the original email
- Use inclusive language and avoid jargon unless appropriate for the recipient
- Proofread for grammar and spelling errors

### 2. Understanding Context
- Carefully read the entire email before drafting a response
- Identify the main request or purpose of the email
- Note any deadlines or time-sensitive information
- Consider the relationship with the sender

### 3. Completeness
- Address all points raised in the original email
- Provide clear and concise answers to questions
- Include relevant information or next steps
- If unable to fully address the request, explain what additional information is needed

### 4. Action Items
- Convert email requests into actionable items when appropriate
- Identify if the email requires follow-up actions
- Determine if approval is needed before taking action
- Create structured tasks for the orchestrator

### 5. Security and Privacy
- Never include sensitive information in responses
- Verify the authenticity of the sender if requesting sensitive information
- Follow company privacy policies when handling personal data
- Flag suspicious emails for human review

## Examples

### Example 1: Customer Inquiry
**Input:**
```
---
type: email
from: customer@example.com
subject: Question about invoice #12345
received: 2026-02-12T10:15:00
priority: high
status: pending
---

## Email Content
Hi, I have a question about my recent invoice #12345. The amount seems higher than expected. Can you please clarify the charges?

Thanks,
John Doe
```

**Output:**
```
---
type: email_response
to: customer@example.com
subject: Re: Question about invoice #12345
status: drafted
---

## Response Content
Dear John,

Thank you for reaching out regarding invoice #12345. I understand your concern about the charges.

I'm reviewing the details of your invoice now and will provide a breakdown of the charges shortly. If there are any discrepancies, I'll make the necessary corrections.

I'll follow up with you within 24 hours with a detailed explanation.

Best regards,
AI Assistant

## Recommended Actions
- [ ] Pull up invoice #12345 from records
- [ ] Verify charges and prepare detailed breakdown
- [ ] Send follow-up email with explanation
```

### Example 2: Urgent Request
**Input:**
```
---
type: email
from: manager@company.com
subject: URGENT: Contract deadline tomorrow
received: 2026-02-12T14:30:00
priority: high
status: pending
---

## Email Content
Need the contract review completed ASAP. Deadline is tomorrow morning. Please prioritize.
```

**Output:**
```
---
type: email_response
to: manager@company.com
subject: Re: URGENT: Contract deadline tomorrow
status: pending_approval
---

## Response Content
Hi [Manager's Name],

I've received your urgent request regarding the contract review. I'm prioritizing this task and will have the review completed and sent to you by early morning tomorrow.

I'll send you an update once the review is complete.

Best regards,
AI Assistant

## Recommended Actions
- [ ] Flag for immediate attention
- [ ] Pull up contract documents
- [ ] Complete review tonight
- [ ] Require approval before sending final response
```

## Common Pitfalls

### 1. Misinterpreting Urgency
- **Pitfall**: Treating all emails with "urgent" as equally critical
- **Solution**: Assess the actual business impact and timeline requirements

### 2. Incomplete Responses
- **Pitfall**: Answering only part of a multi-question email
- **Solution**: Carefully review the original email and ensure all points are addressed

### 3. Tone Mismatch
- **Pitfall**: Using overly formal language with familiar contacts
- **Solution**: Adapt tone to match the relationship and context

### 4. Missing Context Clues
- **Pitfall**: Not recognizing when an email is part of an ongoing conversation
- **Solution**: Look for references to previous communications or shared history

### 5. Over-Automation
- **Pitfall**: Responding to complex situations without human oversight
- **Solution**: Flag nuanced or sensitive topics for human approval

### 6. Privacy Violations
- **Pitfall**: Including confidential information in responses
- **Solution**: Always verify what information can be shared externally

This skill should be used in conjunction with the approval workflow when dealing with sensitive or high-stakes communications.