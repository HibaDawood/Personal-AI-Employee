# Approval Checker Skill

## When to Use This Skill
Use this skill when determining if an action requires human approval in the Silver Tier AI Employee system. This includes:
- Evaluating the sensitivity of proposed actions
- Checking if contacts are in trusted contacts list
- Assessing potential business impact of actions
- Determining approval requirements based on company policy
- Creating approval requests when needed
- Validating approval before executing sensitive actions

## Input/Output Format

### Input
The skill expects input in the following format:
```markdown
---
action_type: email_send, social_post, payment, data_access, file_share
target_contact: contact@example.com
estimated_impact: low/medium/high
sensitivity_level: low/medium/high
is_trusted_contact: true/false
company_policy_requirements: [...]
---

## Action Details
[Specific details about what will be done]

## Potential Risks
[Any identified risks associated with the action]
```

### Output
The skill produces output in the following format:
```markdown
---
action_requires_approval: true/false
approval_reason: [reason for requiring approval]
approval_priority: normal/high/urgent
recommended_approver: [role or person]
---

## Approval Request
[Complete approval request in Pending_Approval/ format]

## Risk Mitigation
- [ ] Verify contact identity
- [ ] Confirm business necessity
- [ ] Validate content appropriateness
```

## Best Practices

### 1. Sensitivity Assessment
- Evaluate the potential impact of each action on business operations
- Consider reputational, financial, and legal implications
- Apply consistent criteria across similar actions
- Document the rationale for approval decisions

### 2. Trust Verification
- Check contacts against the trusted contacts list in Company_Handbook.md
- Verify contact authenticity when possible
- Apply stricter scrutiny to new or unverified contacts
- Maintain updated trusted contacts list

### 3. Policy Adherence
- Follow company policies for different types of actions
- Understand escalation requirements for high-impact actions
- Apply legal and compliance requirements consistently
- Keep policies updated and accessible

### 4. Risk Evaluation
- Assess both immediate and long-term risks
- Consider cumulative impact of multiple related actions
- Evaluate potential for misuse or unintended consequences
- Balance security with operational efficiency

### 5. Clear Communication
- Provide clear justification for approval requirements
- Explain potential consequences of the action
- Specify what aspects need human review
- Make approval process as efficient as possible

### 6. Documentation
- Record all approval decisions and rationale
- Track approval patterns to refine criteria
- Document exceptions and their justifications
- Maintain audit trail for compliance

## Examples

### Example 1: Email to New Contact
**Input:**
```markdown
---
action_type: email_send
target_contact: investor@newcompany.com
estimated_impact: high
sensitivity_level: high
is_trusted_contact: false
company_policy_requirements: ['all_investor_communication_requires_approval']
---

## Action Details
Sending initial outreach email to potential investor expressing interest in partnership opportunity.

## Potential Risks
- Early-stage communication about potential partnership
- Could impact negotiations if not worded carefully
- Represents company to external stakeholder
```

**Output:**
```markdown
---
action_requires_approval: true
approval_reason: Target contact is not in trusted contacts list AND involves investor communication
approval_priority: high
recommended_approver: Business Development Manager
---

## Approval Request
---
type: approval_request
action: email_send
created: 2026-02-12T14:30:00
expires: 2026-02-13T14:30:00
status: pending
priority: high
---

## Action Details
To: investor@newcompany.com
Subject: Partnership Opportunity Discussion
Body: Initial outreach email to potential investor expressing interest in partnership opportunity.

## Risks
This is an initial communication with a potential investor. Improper communication could impact future negotiations.

## To Approve
Move this file to Approved/ folder

## To Reject
Move this file to Rejected/ folder

## To Modify
Edit this file and move to Approved/

## Risk Mitigation
- [ ] Verify contact identity
- [ ] Confirm business necessity
- [ ] Validate content appropriateness
```

### Example 2: Social Media Post
**Input:**
```markdown
---
action_type: social_post
target_platform: LinkedIn
estimated_impact: medium
sensitivity_level: medium
is_trusted_contact: n/a
company_policy_requirements: ['all_public_statements_require_approval']
---

## Action Details
Publishing company announcement about new product launch on official LinkedIn page.

## Potential Risks
- Public statement about company products
- Could affect market perception
- Visible to competitors and customers
```

**Output:**
```markdown
---
action_requires_approval: true
approval_reason: Action is a public statement on social media requiring approval per company policy
approval_priority: high
recommended_approver: Marketing Manager
---

## Approval Request
---
type: approval_request
action: social_post
created: 2026-02-12T15:00:00
expires: 2026-02-13T15:00:00
status: pending
priority: high
---

## Action Details
Platform: LinkedIn
Content: Company announcement about new product launch

## Risks
This is a public statement about company products that could affect market perception.

## To Approve
Move this file to Approved/ folder

## To Reject
Move this file to Rejected/ folder

## To Modify
Edit this file and move to Approved/

## Risk Mitigation
- [ ] Verify content accuracy
- [ ] Confirm alignment with marketing strategy
- [ ] Validate appropriate timing
```

## Common Pitfalls

### 1. Inconsistent Standards
- **Pitfall**: Applying different approval criteria to similar actions
- **Solution**: Develop clear, documented approval framework

### 2. Over-Approving
- **Pitfall**: Requiring approval for low-risk, routine actions
- **Solution**: Create clear thresholds for different approval levels

### 3. Under-Approving
- **Pitfall**: Missing high-risk actions that need approval
- **Solution**: Regular review and refinement of risk assessment criteria

### 4. Unclear Rationale
- **Pitfall**: Not providing clear reasons for approval requirements
- **Solution**: Always document the specific reason for requiring approval

### 5. Outdated Trust Lists
- **Pitfall**: Using outdated trusted contacts list
- **Solution**: Regular updates and verification of trusted contacts

### 6. Ignoring Company Policy
- **Pitfall**: Not considering specific company policies for certain actions
- **Solution**: Integrate policy checks into approval evaluation process

### 7. Insufficient Risk Assessment
- **Pitfall**: Not considering all potential impacts of an action
- **Solution**: Use structured risk assessment framework

This skill should be used consistently for all actions that could have business impact to ensure appropriate oversight and risk management.