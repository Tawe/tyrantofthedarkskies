"""Firebase client for data persistence."""

import firebase_admin
from firebase_admin import credentials, firestore
import os

class FirebaseClient:
    """Handles all Firebase/Firestore operations."""
    
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialize Firebase Admin SDK
        # Try environment variable first (for Fly.io and other cloud deployments)
        import json
        service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
        if service_account_json:
            try:
                service_account = json.loads(service_account_json)
                cred = credentials.Certificate(service_account)
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT environment variable: {e}")
        else:
            # Fallback to file (for local development)
            project_root = os.path.dirname(os.path.dirname(__file__))
            service_account_path = os.path.join(
                project_root,
                'firebase-service-account.json'
            )
            
            if not os.path.exists(service_account_path):
                raise FileNotFoundError(
                    f"Firebase service account not found. Either:\n"
                    f"1. Set FIREBASE_SERVICE_ACCOUNT environment variable with JSON content, or\n"
                    f"2. Place firebase-service-account.json at: {service_account_path}\n"
                    "Download from Firebase Console → Project Settings → Service Accounts"
                )
            
            cred = credentials.Certificate(service_account_path)
        
        firebase_admin.initialize_app(cred)
        self._db = firestore.client()
        self._initialized = True
    
    @property
    def db(self):
        """Get Firestore database instance."""
        return self._db
