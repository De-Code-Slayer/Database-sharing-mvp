#!/usr/bin/env python3
"""
SMTP Connection Test
Tests actual SMTP server connectivity
"""

import os
import smtplib
from dotenv import load_dotenv

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

def test_smtp_connection():
    """Test actual SMTP server connection"""

    # Load environment variables
    load_dotenv()

    print("🔌 Testing SMTP Server Connection")
    print("=" * 40)

    config = SMTPConfig()

    if not config.username or not config.password:
        print("❌ SMTP credentials not configured!")
        return False

    try:
        print(f"Connecting to {config.server}:{config.port}...")

        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.server, config.port)
        else:
            server = smtplib.SMTP(config.server, config.port)
            if config.use_tls:
                server.starttls()

        # Try to login
        server.login(config.username, config.password)
        server.quit()

        print("✅ SMTP connection successful!")
        print("📧 Email sending should work")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP authentication failed!")
        print("💡 Check your SMTP username and password")
        return False
    except smtplib.SMTPConnectError:
        print("❌ SMTP connection failed!")
        print("💡 Check your SMTP server and port settings")
        return False
    except Exception as e:
        print(f"❌ SMTP error: {str(e)}")
        return False

if __name__ == "__main__":
    test_smtp_connection()