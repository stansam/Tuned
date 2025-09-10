from flask import url_for, current_app
from flask_mail import Message
import re
from app.extensions import mail


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_password_reset_email(user, token):
    """Send password reset email to user"""
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        msg = Message(
            subject='Password Reset Request',
            sender=current_app.config['MAIL_NO_REPLY'],
            recipients=[user.email]
        )
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Password Reset Request</h2>
            <p>Hello {user.get_name()},</p>
            <p>You recently requested to reset your password for your account. Click the button below to reset it:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #007bff; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Reset Your Password
                </a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            
            <p><strong>This link will expire in 1 hour.</strong></p>
            
            <p>If you did not request a password reset, please ignore this email or contact support if you have questions.</p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                This is an automated message, please do not reply to this email.
            </p>
        </div>
        """
        
        msg.body = f"""
        Hello {user.get_name()},

        You recently requested to reset your password for your account. 
        Click the link below to reset it:

        {reset_url}

        This link will expire in 1 hour.

        If you did not request a password reset, please ignore this email.
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        return False