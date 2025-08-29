import firebase_admin
from firebase_admin import credentials, storage
import os

# Define the path to your Firebase credentials JSON file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Gets the current directory of this script
CRED_PATH = os.path.join(BASE_DIR, '..', '..', 'client_secret.json')
CRED_PATH = os.path.abspath(CRED_PATH)  # Converts to an absolute path

# Database Docs


# Test if the file exists
if not os.path.exists(CRED_PATH):
    print(f"Error: Firebase credentials file not found at {CRED_PATH}")
else:
    print(f"Firebase credentials file found at {CRED_PATH}")



cred = credentials.Certificate(CRED_PATH)
firebase_admin.initialize_app(cred, {
  "storageBucket": "starter-pack-9fef5.appspot.com" 
})


bucket = storage.bucket()