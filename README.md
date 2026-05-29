# UNC Hussman AI Governance News Monitor

Automated weekly briefing on Fortune 500 AI governance news for the
Hussman School of Journalism and Media AI Governance Audit Project.

## What it does

Every Monday at 9 AM UTC the script:
1. Calls the Anthropic API with web search enabled
2. Searches for Fortune 500 AI governance news from the past 7 days
3. Returns a structured briefing in four sections:
   - Headline incidents
   - New policies and frameworks
   - Regulatory and legal developments
   - Worth watching
4. Sends the briefing as a formatted HTML email to all recipients

## Setup (one time, takes ~10 minutes)

### Step 1 - Fork or create a GitHub repository
Upload these three files to a new private GitHub repository:
- monitor.py
- requirements.txt
- .github/workflows/weekly_briefing.yml

### Step 2 - Add your secrets
In GitHub: Settings > Secrets and variables > Actions > New repository secret

Add these four secrets:

| Secret name       | Value                                      |
|-------------------|--------------------------------------------|
| ANTHROPIC_API_KEY | Your Anthropic API key from console.anthropic.com |
| EMAIL_SENDER      | Your Gmail address (e.g. you@gmail.com)    |
| EMAIL_PASSWORD    | A Gmail App Password (not your login password) |
| EMAIL_RECIPIENTS  | Comma-separated list of recipient emails   |

### Step 3 - Get a Gmail App Password
1. Go to myaccount.google.com
2. Security > 2-Step Verification (must be enabled)
3. Search "App passwords" at the top
4. Create a new app password called "Governance Monitor"
5. Copy the 16-character password into the EMAIL_PASSWORD secret

### Step 4 - Test it
In your GitHub repository go to:
Actions > Weekly AI Governance Briefing > Run workflow

This runs it immediately so you can confirm the email arrives before
waiting for the Monday schedule.

## Schedule

Runs every Monday at 9:00 AM UTC (5:00 AM Eastern, 2:00 AM Pacific).
To change the time, edit the cron line in weekly_briefing.yml.
Cron format: minute hour day month weekday
Example for Monday 8 AM Eastern (1 PM UTC): 0 13 * * 1

## Cost

Each run uses approximately 2,000 to 4,000 tokens plus web search calls.
At current Anthropic pricing this is under $0.05 per weekly run.
GitHub Actions free tier includes 2,000 minutes per month, far more than needed.

## Troubleshooting

- Email not arriving: Check spam folder. Verify Gmail App Password is correct.
- API error: Confirm ANTHROPIC_API_KEY secret is set and valid.
- View run logs: GitHub > Actions > click the most recent run > send-briefing job
