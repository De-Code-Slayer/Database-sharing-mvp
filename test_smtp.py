#!/usr/bin/env python3
"""
Standalone SMTP Configuration Test
Tests SMTP configuration without importing the full Flask app
"""

import os
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

def test_smtp_config():
    """Test SMTP configuration loading"""

    # Load environment variables
    load_dotenv()

    print("📧 Testing SMTP Configuration")
    print("=" * 40)

    config = SMTPConfig()

    print(f"SMTP Server: {config.server}")
    print(f"SMTP Port: {config.port}")
    print(f"Username: {'✅ Set' if config.username else '❌ Not set'}")
    print(f"Password: {'✅ Set' if config.password else '❌ Not set'}")
    print(f"Use TLS: {config.use_tls}")
    print(f"Use SSL: {config.use_ssl}")
    print(f"Default Sender: {config.default_sender}")
    print(f"App Name: {config.app_name}")

    # Check if basic config is available
    if config.username and config.password:
        print("\n✅ SMTP configuration is complete!")
        print("📨 Ready to send emails")
    else:
        print("\n❌ SMTP configuration incomplete!")
        print("📝 Add SMTP_USERNAME and SMTP_PASSWORD to your .env file")

    return config

if __name__ == "__main__":
    test_smtp_config()