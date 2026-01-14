"""
Example usage of the SMTP module

This file demonstrates how to use the SMTP functionality in the Database Sharing Platform.
"""

from app.views.utilities.smtp import (
    send_mail,
    send_welcome_email,
    send_password_reset_email,
    send_invoice_email,
    SMTPConfig
)

# Example 1: Send a basic email
def example_basic_email():
    """Send a basic email with text content"""
    success = send_mail(
        to_email="chukwujapheth232@gmail.com",
        subject="Test Email",
        body="This is a test email sent from the Database Sharing Platform."
    )
    return success

# Example 2: Send an HTML email
def example_html_email():
    """Send an email with HTML content"""
    success = send_mail(
        to_email="chukwujapheth232@gmail.com",
        subject="Welcome!",
        html_body="""
        <h1>Welcome!</h1>
        <p>This is a <strong>HTML</strong> email.</p>
        <p>Visit <a href="https://smallshardz.com">our website</a> for more info.</p>
        """
    )
    return success

# Example 3: Send email with template
def example_template_email():
    """Send an email using a template"""
    success = send_mail(
        to_email="chukwujapheth232@gmail.com",
        subject="Custom Message",
        template="welcome",  # Uses templates/emails/welcome.html and welcome.txt
        template_vars={
            'username': 'John Doe',
            'login_url': 'https://dashboard.smallshardz.com/login'
        }
    )
    return success

# Example 4: Send email with attachments
def example_email_with_attachments():
    """Send an email with file attachments"""
    success = send_mail(
        to_email="chukwujapheth232@gmail.com",
        subject="Report Attached",
        body="Please find the attached report.",
        attachments=["/path/to/report.pdf", "/path/to/data.csv"]
    )
    return success

# Example 5: Using predefined email functions
def example_predefined_emails():
    """Use the predefined email functions"""

    # Welcome email
    send_welcome_email("chukwujapheth232@gmail.com", "John Doe")

    # Password reset email
    send_password_reset_email("chukwujapheth232@gmail.com", "reset-token-123", "John Doe")

    # Invoice email
    invoice_data = {
        'id': 'INV-001',
        'amount': 29.99,
        'period_start': '2024-01-01',
        'period_end': '2024-01-31',
        'status': 'unpaid',
        'description': 'Monthly database hosting'
    }
    send_invoice_email("chukwujapheth232@gmail.com", invoice_data)

# Example 6: Check SMTP configuration
def check_smtp_config():
    """Check if SMTP is properly configured"""
    config = SMTPConfig()
    print(f"SMTP Server: {config.server}")
    print(f"SMTP Port: {config.port}")
    print(f"Username configured: {bool(config.username)}")
    print(f"Password configured: {bool(config.password)}")
    print(f"Default sender: {config.default_sender}")
    print(f"App name: {config.app_name}")

if __name__ == "__main__":
    # Run configuration check
    check_smtp_config()
    # Send example emails
    example_basic_email()
    example_html_email()
    example_template_email()
    example_email_with_attachments()
    example_predefined_emails()
    