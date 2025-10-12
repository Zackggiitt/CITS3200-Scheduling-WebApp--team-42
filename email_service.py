import boto3
from botocore.exceptions import ClientError
import os
import urllib.parse
import string 
import random
from datetime import datetime, timedelta
from models import db, User


class EmailToken(db.Model):
    """Model to store email verification tokens"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    token_type = db.Column(db.String(50), nullable=False)  # welcome, password_reset, etc.
    used = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<EmailToken {self.email} ({self.token_type})>'


def generate_token(length=32):
    """Generate a random token for security purposes"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def valid_email(email):
    """Basic email validation"""
    # Check if the email contains one "@" symbol
    if email.count('@') != 1:
        return False

    # Split the email into local part and domain part
    local_part, domain_part = email.split('@')

    # Check if both the local part and domain part are not empty
    if len(local_part) == 0 or len(domain_part) == 0:
        return False

    # Check if the domain part contains a dot (.)
    if domain_part.find('.') == -1:
        return False

    return True


def send_welcome_email(recipient_email, recipient_name=None, base_url=None, user_role=None):
    """Send an account setup email to a new UC or FAC account"""
    # Check if we're in mock mode
    use_mock = os.environ.get('USE_MOCK_EMAIL', 'false').lower() == 'true'
    
    # Only validate sender email if not in mock mode
    if not use_mock:
        sender_email = os.environ.get('SES_SENDER_EMAIL')
        
        if not sender_email:
            print("SES_SENDER_EMAIL environment variable not set")
            return False
        
        if not valid_email(sender_email):
            print(f"Invalid sender email address: {sender_email}")
            return False
    else:
        # In mock mode, use a dummy sender email
        sender_email = "noreply@example.com"
        
    if not valid_email(recipient_email):
        print(f"Invalid email address: {recipient_email}")
        return False

    # Generate and store token
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(days=7)  # Token expires in 7 days
    
    email_token = EmailToken(
        email=recipient_email,
        token=token,
        expires_at=expires_at,
        token_type='account_setup'
    )
    
    try:
        db.session.add(email_token)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error storing email token: {e}")
        return False

    # Get base URL for the setup link
    if not base_url:
        base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Create setup link with token
    setup_link = f"{base_url}/setup-account?token={token}"

    # Customize message based on role
    from models import UserRole
    if user_role == UserRole.UNIT_COORDINATOR:
        role_message = "The administrator has added you as a Unit Coordinator for the Scheduling System. As a Unit Coordinator, you will be able to manage your units, add facilitators, and create schedules."
        subject = "Set Up Your Unit Coordinator Account"
    else:  # Facilitator
        role_message = "Your Unit Coordinator has added you to the Scheduling System as a Facilitator. You will be able to view your assigned sessions and manage your availability."
        subject = "Set Up Your Facilitator Account"
    
    # Plain text version
    body_text = (
        f"Hello,\n\n"
        f"{role_message}\n\n"
        f"To complete your account setup and create your password, please click the link below:\n"
        f"{setup_link}\n\n"
        f"This link will expire in 7 days.\n\n"
        f"Best regards,\n"
        f"Your Scheduling Team\n"
    )

    # HTML version
    body_html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }}
            .container {{
                width: 100%;
                padding: 20px;
            }}
            .header {{
                background-color: #007bff;
                color: white;
                padding: 10px 0;
                text-align: center;
            }}
            .content {{
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                margin: 20px 0;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                text-align: center;
                color: #888;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{"Set Up Your Unit Coordinator Account" if user_role == UserRole.UNIT_COORDINATOR else "Set Up Your Facilitator Account"}</h1>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>{role_message}</p>
                <p>To complete your account setup and create your password, please click the button below:</p>
                <p style="text-align: center;">
                    <a href="{setup_link}" class="button">Set Up My Account</a>
                </p>
                <p style="font-size: 12px; color: #666;">
                    Or copy and paste this link into your browser:<br>
                    {setup_link}
                </p>
                <p style="font-size: 12px; color: #666;">
                    This link will expire in 7 days.
                </p>
                <p>Best regards,<br>Your Scheduling Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Scheduling System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Check if we should mock emails (for development)
    if os.environ.get('USE_MOCK_EMAIL') == 'true':
        print(f"Mock email sent to {recipient_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body_text}")
        return True

    # Send email via AWS SES
    try:
        # Support both naming conventions for AWS credentials
        aws_key = os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('AWS_ACCESS_KEY')
        aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        ses_client = boto3.client(
            'ses',
            region_name=os.environ.get('SES_REGION', 'ap-southeast-1'),
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret
        )

        CHARSET = "UTF-8"
        response = ses_client.send_email(
            Destination={
                'ToAddresses': [recipient_email],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': body_html,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject,
                },
            },
            Source=sender_email,
        )
        print(f"Email sent successfully to {recipient_email}")
        print(f"Message ID: {response['MessageId']}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error sending email: {error_code} - {error_message}")
        return False
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        return False


def verify_email_token(token, token_type='account_setup'):
    """Verify an email token and return the associated email if valid"""
    email_token = EmailToken.query.filter_by(
        token=token, 
        token_type=token_type,
        used=False
    ).first()
    
    if not email_token:
        return None
    
    # Check if token has expired
    if email_token.expires_at < datetime.utcnow():
        return None
    
    return email_token.email


def mark_token_as_used(token):
    """Mark an email token as used"""
    email_token = EmailToken.query.filter_by(token=token, used=False).first()
    
    if not email_token:
        return False
    
    email_token.used = True
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error marking token as used: {e}")
        return False
