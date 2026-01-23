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
        # Look for service account file in project root (one level up from firebase package)
        project_root = os.path.dirname(os.path.dirname(__file__))
        service_account_path = os.path.join(
            project_root,
            'firebase-service-account.json'
        )
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Firebase service account file not found: {service_account_path}\n"
                "Please download it from Firebase Console → Project Settings → Service Accounts"
            )
        
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        self._db = firestore.client()
        self._initialized = True
    
    @property
    def db(self):
        """Get Firestore database instance."""
        return self._db
