# Email System Setup

## Quick Start Guide

### Step 1: Install Dependencies

```bash
pip install boto3
```

### Step 2: Create the Database Table

Run the migration to create the `email_token` table:

```bash
flask db upgrade
```

Or if you're not using Flask-Migrate:

```bash
python -c "from application import app, db; app.app_context().push(); db.create_all()"
```

### Step 3: Configure Environment Variables

For **testing without AWS** (recommended first):

```bash
export USE_MOCK_EMAIL=true
```

For **production with AWS SES**:

```bash
export USE_MOCK_EMAIL=false
export SES_SENDER_EMAIL=your-verified-email@example.com
export SES_REGION=ap-southeast-1
export AWS_ACCESS_KEY=YOUR_AWS_ACCESS_KEY_HERE
export AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY_HERE
```

Or create a `.env` file:

```
# For local testing
USE_MOCK_EMAIL=true

# For production on AWS (use the shared credentials from the instance)
# USE_MOCK_EMAIL=false
SES_SENDER_EMAIL=your-verified-email@example.com
SES_REGION=ap-southeast-1
AWS_ACCESS_KEY=YOUR_AWS_ACCESS_KEY_HERE
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY_HERE
```

**Note**: The code supports both `AWS_ACCESS_KEY` and `AWS_ACCESS_KEY_ID` for compatibility.

### Step 4: Test the System

Run the test script to verify everything is working:

```bash
python test_email_system.py
```

## AWS SES Configuration (For Production)

### Required Environment Variables

1. `SES_SENDER_EMAIL` - The verified sender email address in AWS SES
2. `SES_REGION` - AWS region (default: ap-southeast-1)
3. `AWS_ACCESS_KEY_ID` - Your AWS access key
4. `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
5. `USE_MOCK_EMAIL` - Set to 'false' for real emails, 'true' for testing

## How It Works

The email system automatically sends welcome emails when you create new UC or FAC accounts using the CLI scripts:

- `add_uc.py` - Creates a Unit Coordinator account and sends a welcome email
- `add_facilitator.py` - Creates a Facilitator account and sends a welcome email

## Email Verification

When a welcome email is sent, a verification token is stored in the database. Users can verify their email by using the token.

## Testing

To test the email system without actually sending emails, set the environment variable:

```
USE_MOCK_EMAIL=true
```

This will print email content to the console instead of sending real emails.

## Usage Examples

### Create a Unit Coordinator with Welcome Email

```bash
python add_uc.py --email new_uc@example.com --first John --last Doe --password securepassword123
```

### Create a Facilitator with Welcome Email

```bash
python add_facilitator.py --email new_facilitator@example.com --first Jane --last Smith --password securepassword123
```
