# LinkedIn Poster Skill

## When to Use This Skill
Use this skill when creating or managing LinkedIn posts for the Silver Tier AI Employee system. This includes:
- Creating engaging business content for LinkedIn
- Scheduling posts according to company guidelines
- Incorporating relevant hashtags and mentions
- Ensuring posts align with brand voice and messaging
- Managing LinkedIn engagement and responses

## Input/Output Format

### Input
The skill expects input in the following format:
```markdown
---
type: linkedin_post
content: |
  Your post content here
  Can be multiple lines
hashtags: ['business', 'AI', 'automation']
mentions: ['@company', '@person']
image_path: /path/to/image.jpg (optional)
scheduled_time: immediate OR 2026-02-12T18:00:00
status: pending_approval
---

## Post Content
Detailed content for the LinkedIn post...
```

### Output
The skill produces output in the following format:
```markdown
---
type: linkedin_post_published
post_id: linkedin_post_identifier
published_at: 2026-02-12T15:30:00
status: published/draft/failed
---

## Published Content
The final version of the post that was published...

## Engagement Strategy
- [ ] Monitor comments
- [ ] Respond to initial comments
- [ ] Share with team members
```

## Best Practices

### 1. Professional Tone
- Maintain a professional, business-oriented tone
- Use industry-relevant terminology appropriately
- Keep content informative and valuable to the audience
- Avoid overly casual language or slang

### 2. Value-Driven Content
- Focus on providing value to the LinkedIn community
- Share insights, tips, or industry news
- Include actionable advice when possible
- Connect content to real business outcomes

### 3. Engagement Optimization
- Ask questions to encourage comments
- Use relevant hashtags (typically 3-5)
- Tag relevant individuals or companies when appropriate
- Include a clear call-to-action when relevant

### 4. Visual Elements
- Use high-quality, professional images
- Ensure images are properly sized for LinkedIn (1200x627px recommended for link previews)
- Include alt text for accessibility
- Make sure visuals complement the text content

### 5. Timing and Frequency
- Post during peak engagement hours (typically Tuesday-Thursday, 8-10am or 12-2pm)
- Maintain consistent posting frequency
- Avoid overposting (no more than 1 post per day)
- Consider time zones when scheduling

### 6. Compliance and Brand Alignment
- Ensure all content aligns with company brand guidelines
- Follow LinkedIn's community standards
- Avoid promotional content that looks like spam
- Include appropriate disclaimers when necessary

## Examples

### Example 1: Industry Insight Post
**Input:**
```markdown
---
type: linkedin_post
content: |
  The future of AI in business operations is rapidly evolving. Companies that embrace automation today are positioning themselves for competitive advantage tomorrow.
  
  Key trends to watch:
  1. Intelligent process automation
  2. Predictive analytics integration
  3. Enhanced customer experiences
  
  What trends are you seeing in your industry?
hashtags: ['AI', 'Automation', 'Business', 'Innovation']
mentions: []
image_path: ./images/ai-business-future.jpg
scheduled_time: immediate
status: pending_approval
---
```

**Output:**
```markdown
---
type: linkedin_post_published
post_id: abc123xyz
published_at: 2026-02-12T15:30:00
status: published
---

## Published Content
The future of AI in business operations is rapidly evolving. Companies that embrace automation today are positioning themselves for competitive advantage tomorrow.

Key trends to watch:
1. Intelligent process automation
2. Predictive analytics integration
3. Enhanced customer experiences

What trends are you seeing in your industry?

#AI #Automation #Business #Innovation

## Engagement Strategy
- [ ] Monitor comments for the next 2 hours
- [ ] Respond to initial comments
- [ ] Share with team members
```

### Example 2: Company Milestone Post
**Input:**
```markdown
<thumbnail>
---
type: linkedin_post
content: |
  Excited to announce that we've reached a major milestone - 1000+ clients trusting us with their business automation needs!

  This achievement wouldn't be possible without our amazing team and valued clients. Here's to the next chapter of growth and innovation.

  #CompanyMilestone #Gratitude #Growth #Automation
hashtags: ['CompanyMilestone', 'Gratitude', 'Growth', 'Automation']
mentions: []
image_path: ./images/milestone-celebration.jpg
scheduled_time: 2026-02-12T09:00:00
status: pending_approval
---
</thumbnail>
```

**Output:**
```markdown
---
type: linkedin_post_published
post_id: def456uvw
published_at: 2026-02-12T09:00:00
status: published
---

## Published Content
Excited to announce that we've reached a major milestone - 1000+ clients trusting us with their business automation needs!

This achievement wouldn't be possible without our amazing team and valued clients. Here's to the next chapter of growth and innovation.

#CompanyMilestone #Gratitude #Growth #Automation

## Engagement Strategy
- [ ] Monitor comments throughout the day
- [ ] Thank people who engage with the post
- [ ] Share with team members
```

## Common Pitfalls

### 1. Over-Promotion
- **Pitfall**: Making every post a direct sales pitch
- **Solution**: Follow the 80/20 rule - 80% value-driven content, 20% promotional

### 2. Irrelevant Hashtags
- **Pitfall**: Using trending hashtags unrelated to content
- **Solution**: Use only relevant, industry-specific hashtags

### 3. Poor Timing
- **Pitfall**: Posting at times with low engagement
- **Solution**: Schedule posts for optimal engagement times

### 4. Generic Content
- **Pitfall**: Creating content that could apply to any company
- **Solution**: Make content specific to your company's expertise and values

### 5. Ignoring Engagement
- **Pitfall**: Publishing and forgetting about the post
- **Solution**: Actively monitor and engage with comments after posting

### 6. Inconsistent Voice
- **Pitfall**: Changing tone or messaging style frequently
- **Solution**: Maintain consistent brand voice across all posts

### 7. Not Following Platform Guidelines
- **Pitfall**: Violating LinkedIn's community standards
- **Solution**: Regularly review LinkedIn's posting guidelines

This skill should be used in conjunction with the approval workflow for all business-critical or potentially controversial content.