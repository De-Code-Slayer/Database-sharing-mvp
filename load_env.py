#!/usr/bin/env python3
"""
Environment Loader and Checker
Loads environment variables from .env file and displays current configuration
"""

import os
from dotenv import load_dotenv

def load_and_check_env():
    """Load environment variables and display current configuration"""

    # Load environment variables
    load_dotenv()

    print("🔧 Environment Variables Loaded")
    print("=" * 50)

    # Core Flask settings
    print("📱 Flask Configuration:")
    print(f"  FLASK_ENV: {os.getenv('FLASK_ENV', 'Not set')}")
    print(f"  FLASK_DEBUG: {os.getenv('FLASK_DEBUG', 'Not set')}")
    print(f"  FLASK_RUN_HOST: {os.getenv('FLASK_RUN_HOST', 'Not set')}")
    print(f"  FLASK_RUN_PORT: {os.getenv('FLASK_RUN_PORT', 'Not set')}")
    print(f"  SECRET_KEY: {'✅ Set' if os.getenv('SECRET_KEY') else '❌ Not set'}")
    print(f"  SERVER_NAME: {os.getenv('SERVER_NAME', 'Not set')}")

    print("\n🗄️ Database Configuration:")
    db_url = os.getenv('DATABASE_URL', 'Not set')
    if db_url != 'Not set':
        # Mask password in URL for security
        if '@' in db_url:
            masked_url = db_url.split('@')[0].split(':')[0] + ':***@' + db_url.split('@')[1]
            print(f"  DATABASE_URL: {masked_url}")
        else:
            print(f"  DATABASE_URL: {db_url}")
    else:
        print(f"  DATABASE_URL: {db_url}")

    print(f"  DB_HOST: {os.getenv('DB_HOST', 'Not set')}")

    print("\n📧 SMTP Configuration:")
    print(f"  SMTP_SERVER: {os.getenv('SMTP_SERVER', 'Not set')}")
    print(f"  SMTP_PORT: {os.getenv('SMTP_PORT', 'Not set')}")
    print(f"  SMTP_USERNAME: {'✅ Set' if os.getenv('SMTP_USERNAME') else '❌ Not set'}")
    print(f"  SMTP_PASSWORD: {'✅ Set' if os.getenv('SMTP_PASSWORD') else '❌ Not set'}")
    print(f"  SMTP_DEFAULT_SENDER: {os.getenv('SMTP_DEFAULT_SENDER', 'Not set')}")

    print("\n💳 Payment Configuration:")
    print(f"  PAYSTACK_PUBLIC_KEY: {'✅ Set' if os.getenv('PAYSTACK_PUBLIC_KEY') else '❌ Not set'}")

    print("\n🔐 OAuth Configuration:")
    print(f"  GOOGLE_CLIENT_ID: {'✅ Set' if os.getenv('GOOGLE_CLIENT_ID') else '❌ Not set'}")
    print(f"  GOOGLE_CLIENT_SECRET: {'✅ Set' if os.getenv('GOOGLE_CLIENT_SECRET') else '❌ Not set'}")
    print(f"  GITHUB_CLIENT_ID: {'✅ Set' if os.getenv('GITHUB_CLIENT_ID') else '❌ Not set'}")
    print(f"  GITHUB_CLIENT_SECRET: {'✅ Set' if os.getenv('GITHUB_CLIENT_SECRET') else '❌ Not set'}")

    print("\n💾 Storage Configuration:")
    print(f"  STORAGE_ROOT: {os.getenv('STORAGE_ROOT', 'Not set')}")

    print("\n🔑 Security:")
    print(f"  VPS_PASSWORD: {'✅ Set' if os.getenv('VPS_PASSWORD') else '❌ Not set'}")
    print(f"  AWS_PASS: {'✅ Set' if os.getenv('AWS_PASS') else '❌ Not set'}")

    print("\n✅ Environment loading complete!")
    print("💡 Tip: Add any missing SMTP settings to enable email functionality")

if __name__ == "__main__":
    load_and_check_env()