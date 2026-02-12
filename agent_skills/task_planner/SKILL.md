# Task Planner Skill

## When to Use This Skill
Use this skill when creating structured plans for task execution in the Silver Tier AI Employee system. This includes:
- Breaking down complex tasks into manageable steps
- Creating execution plans with clear objectives
- Identifying required resources and dependencies
- Determining if approval is needed for specific actions
- Establishing checkpoints and success criteria

## Input/Output Format

### Input
The skill expects input in the following format:
```markdown
---
task_id: EMAIL_xyz OR WHATSAPP_abc
created: 2026-02-12T10:30:00
status: pending
requires_approval: true/false
---

## Task Details
[Clear description of what needs to be done]

## Available Resources
- Company_Handbook.md for tone/rules
- Previous similar tasks in Done/
- External APIs and services
```

### Output
The skill produces output in the following format:
```markdown
---
task_id: EMAIL_xyz
created: 2026-02-12T10:30:00
status: planned
requires_approval: true
---

## Objective
[Clear description of what needs to be done]

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

## Success Criteria
- [ ] Task completed according to requirements
- [ ] Proper documentation created
- [ ] Stakeholders notified if needed
```

## Best Practices

### 1. Clear Objectives
- Define the primary goal of the task in simple, actionable terms
- Ensure the objective aligns with business priorities
- Make the objective measurable and achievable
- Consider the end-user impact of the task

### 2. Logical Step Sequencing
- Order steps in a logical sequence that builds upon previous steps
- Ensure each step is clearly defined and actionable
- Include validation steps between major phases
- Plan for potential roadblocks and alternatives

### 3. Resource Identification
- List all required resources before starting the plan
- Identify dependencies between different resources
- Consider availability and access limitations
- Plan for backup resources if primary ones are unavailable

### 4. Approval Decision Framework
- Evaluate sensitivity of the task (financial, legal, PR implications)
- Check if the recipient/contact is in trusted contacts list
- Consider company policy requirements for specific actions
- Apply consistent approval criteria across similar tasks

### 5. Risk Assessment
- Identify potential failure points in the execution plan
- Plan mitigation strategies for high-risk steps
- Consider impact of failure on other systems/processes
- Include rollback procedures when appropriate

### 6. Success Measurement
- Define clear, measurable criteria for task success
- Include both functional and quality requirements
- Plan for verification and validation steps
- Consider long-term impact and sustainability

## Examples

### Example 1: Email Response Task
**Input:**
```markdown
---
task_id: EMAIL_john_doe_20260212_143000
created: 2026-02-12T14:30:00
status: pending
requires_approval: false
---

## Task Details
Respond to customer inquiry about delayed shipment. Customer is concerned about missed delivery deadline for important event.

## Available Resources
- Company_Handbook.md for tone/rules
- Previous similar tasks in Done/
- Shipping tracking information
```

**Output:**
```markdown
---
task_id: EMAIL_john_doe_20260212_143000
created: 2026-02-12T14:30:00
status: planned
requires_approval: true
---

## Objective
Address customer concerns about delayed shipment and provide reassurance with concrete next steps.

## Steps
- [ ] Step 1: Verify shipping status and identify delay cause
- [ ] Step 2: Draft empathetic response with clear timeline
- [ ] Step 3: Get approval (customer is important, delay significant)
- [ ] Step 4: Send response and update tracking
- [ ] Step 5: Log interaction and follow up in 24 hours

## Resources Needed
- Company_Handbook.md for tone/rules
- Shipping system access
- Previous similar tasks in Done/

## Approval Required For
- Final response content (due to customer importance)

## Success Criteria
- [ ] Customer receives timely, empathetic response
- [ ] Clear timeline for resolution provided
- [ ] Customer satisfaction maintained
- [ ] Follow-up scheduled and completed
```

### Example 2: Social Media Post Task
**Input:**
```markdown
---
task_id: LINKEDIN_post_20260212_150000
created: 2026-02-12T15:00:00
status: pending
requires_approval: true
---

## Task Details
Create and publish LinkedIn post about company's new sustainability initiative.

## Available Resources
- Company_Handbook.md for tone/rules
- Marketing guidelines document
- Sustainability report
```

**Output:**
```markdown
---
task_id: LINKEDIN_post_20260212_150000
created: 2026-02-12T15:00:00
status: planned
requires_approval: true
---

## Objective
Publish engaging LinkedIn post highlighting company's sustainability efforts to enhance brand reputation.

## Steps
- [ ] Step 1: Review sustainability report and marketing guidelines
- [ ] Step 2: Draft post content with compelling headline
- [ ] Step 3: Select appropriate visual content
- [ ] Step 4: Get approval (public-facing content)
- [ ] Step 5: Schedule publication and monitor engagement

## Resources Needed
- Company_Handbook.md for tone/rules
- Marketing guidelines document
- Sustainability report
- LinkedIn posting tools

## Approval Required For
- All content before publication (brand representation)

## Success Criteria
- [ ] Post published according to schedule
- [ ] Content aligns with brand guidelines
- [ ] Positive engagement metrics achieved
- [ ] No compliance issues reported
```

## Common Pitfalls

### 1. Overcomplicating Steps
- **Pitfall**: Creating too many granular steps that slow down execution
- **Solution**: Balance detail with efficiency; group related actions

### 2. Missing Critical Dependencies
- **Pitfall**: Not identifying all required resources upfront
- **Solution**: Conduct thorough resource assessment during planning

### 3. Inconsistent Approval Logic
- **Pitfall**: Applying different approval criteria to similar tasks
- **Solution**: Develop clear, documented approval framework

### 4. Unrealistic Timelines
- **Pitfall**: Setting expectations that don't account for actual execution time
- **Solution**: Factor in time for reviews, approvals, and potential delays

### 5. Incomplete Success Criteria
- **Pitfall**: Defining success in only binary terms (done/not done)
- **Solution**: Include quality and impact measures in success criteria

### 6. Ignoring Risk Factors
- **Pitfall**: Not planning for potential failures or obstacles
- **Solution**: Include contingency plans and rollback procedures

### 7. Unclear Objectives
- **Pitfall**: Creating plans for vaguely defined tasks
- **Solution**: Clarify objectives before developing detailed steps

This skill should be applied consistently to all tasks entering the Needs_Action/ folder to ensure systematic and reliable execution.