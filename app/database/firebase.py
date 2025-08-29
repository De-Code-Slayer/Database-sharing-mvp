import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("path/to/your/firebase/credentials.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'your-firebase-bucket.appspot.com'
})


bucket = storage.bucket()