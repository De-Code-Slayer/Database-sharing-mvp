"""
SMTP Email Module for Database Sharing Platform

This module provides email functionality using SMTP. To configure:

Environment Variables:
- SMTP_SERVER: SMTP server hostname (default: smtp.gmail.com)
- SMTP_PORT: SMTP server port (default: 587)
- SMTP_USERNAME: SMTP username/email
- SMTP_PASSWORD: SMTP password/app password
- SMTP_USE_TLS: Use TLS encryption (default: true)
- SMTP_USE_SSL: Use SSL encryption (default: false)
- SMTP_DEFAULT_SENDER: Default sender email (default: noreply@smallshardz.com)
- APP_NAME: Application name for emails (default: SmallShardz)

Example .env configuration:
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_DEFAULT_SENDER=noreply@smallshardz.com
APP_NAME=SmallShardz

For Gmail, use an "App Password" instead of your regular password.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import render_template
from app.logger import logger


class SMTPConfig:
    """SMTP configuration class"""
    def __init__(self):
        self.server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
        self.default_sender = os.getenv("SMTP_DEFAULT_SENDER", "noreply@smallshardz.com")
        self.app_name = os.getenv("APP_NAME", "SmallShardz")


def send_mail(
    to_email,
    subject,
    body=None,
    html_body=None,
    template=None,
    template_vars=None,
    attachments=None,
    sender=None
):
    """
    Send email using SMTP

    Args:
        to_email (str or list): Recipient email(s)
        subject (str): Email subject
        body (str): Plain text body
        html_body (str): HTML body
        template (str): Template name to render (without .html)
        template_vars (dict): Variables for template rendering
        attachments (list): List of file paths to attach
        sender (str): Custom sender email

    Returns:
        bool: True if sent successfully, False otherwise
    """
    config = SMTPConfig()

    if not config.username or not config.password:
        logger.error("SMTP credentials not configured")
        return False

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = sender or config.default_sender

        # Handle recipients
        if isinstance(to_email, str):
            msg['To'] = to_email
            recipients = [to_email]
        else:
            msg['To'] = ", ".join(to_email)
            recipients = to_email

        # Prepare body content
        if template:
            # Render template
            template_vars = template_vars or {}
            template_vars.setdefault('app_name', config.app_name)

            if html_body is None:
                html_body = render_template(f"emails/{template}.html", **template_vars)
            if body is None:
                body = render_template(f"emails/{template}.txt", **template_vars)
        elif html_body and not body:
            # Generate plain text from HTML (basic conversion)
            import re
            body = re.sub(r'<[^>]+>', '', html_body).strip()

        # Add plain text part
        if body:
            msg.attach(MIMEText(body, 'plain'))

        # Add HTML part
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        # Add attachments
        if attachments:
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        filename = os.path.basename(attachment_path)
                        part.add_header('Content-Disposition',
                                      f'attachment; filename="{filename}"')
                        msg.attach(part)

        # Send email
        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.server, config.port)
        else:
            server = smtplib.SMTP(config.server, config.port)
            if config.use_tls:
                server.starttls()

        server.login(config.username, config.password)
        server.sendmail(msg['From'], recipients, msg.as_string())
        server.quit()

        logger.info(f"Email sent successfully to {recipients}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def send_welcome_email(user_email, username):
    """Send welcome email to new user"""
    return send_mail(
        to_email=user_email,
        subject=f"Welcome to {SMTPConfig().app_name}!",
        template="welcome",
        template_vars={
            'username': username,
            'login_url': "https://dashboard.smallshardz.com/login"
        }
    )


def send_password_reset_email(user_email, reset_token, username):
    """Send password reset email"""
    return send_mail(
        to_email=user_email,
        subject=f"Password Reset - {SMTPConfig().app_name}",
        template="password_reset",
        template_vars={
            'username': username,
            'reset_url': f"https://auth.smallshardz.com/auth/reset/{reset_token}",
            'token': reset_token
        }
    )


def send_invoice_email(user_email, invoice_data):
    """Send invoice notification email"""
    return send_mail(
        to_email=user_email,
        subject=f"Invoice #{invoice_data['id']} - {SMTPConfig().app_name}",
        template="invoice",
        template_vars=invoice_data
    )


def send_payment_confirmation_email(user_email, payment_data):
    """Send payment confirmation email"""
    return send_mail(
        to_email=user_email,
        subject=f"Payment Confirmed - {SMTPConfig().app_name}",
        template="payment_confirmation",
        template_vars=payment_data
    )


def send_database_created_email(user_email, db_data):
    """Send database creation confirmation email"""
    return send_mail(
        to_email=user_email,
        subject=f"Database Created - {SMTPConfig().app_name}",
        template="database_created",
        template_vars=db_data
    )


def send_storage_limit_warning_email(user_email, usage_data):
    """Send storage limit warning email"""
    return send_mail(
        to_email=user_email,
        subject=f"Storage Limit Warning - {SMTPConfig().app_name}",
        template="storage_warning",
        template_vars=usage_data
    )