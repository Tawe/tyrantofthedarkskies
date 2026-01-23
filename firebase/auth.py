"""Firebase Authentication integration for MUD server."""

from firebase_admin import auth
from .client import FirebaseClient
from typing import Optional, Dict
import re
import requests
import json

class FirebaseAuth:
    """Handles Firebase Authentication for players."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseAuth, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialize Firebase client (which initializes Firebase Admin)
        self.client = FirebaseClient()
        self._initialized = True
        
        # Get API key from service account (needed for REST API)
        try:
            import os
            # Look for service account file in project root (one level up from firebase package)
            project_root = os.path.dirname(os.path.dirname(__file__))
            service_account_path = os.path.join(
                project_root,
                'firebase-service-account.json'
            )
            if os.path.exists(service_account_path):
                with open(service_account_path, 'r') as f:
                    service_account = json.load(f)
                    # We'll need the project ID, not API key for Admin SDK
                    # For REST API password verification, we need the Web API Key
                    # This should be set as an environment variable or config
                    self.project_id = service_account.get('project_id')
        except Exception as e:
            print(f"Warning: Could not load Firebase config: {e}")
            self.project_id = None
    
    def create_user(self, email: str, password: str, display_name: str) -> Optional[Dict]:
        """
        Create a new Firebase user.
        Returns user data dict or None on error.
        """
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False  # Can be verified later
            )
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name
            }
        except Exception as e:
            print(f"Error creating Firebase user: {e}")
            return None
    
    def verify_password(self, email: str, password: str, api_key: Optional[str] = None) -> Optional[Dict]:
        """
        Verify user credentials using Firebase REST API.
        Requires Web API Key from Firebase Console.
        """
        if not api_key:
            # Try to get from environment variable
            import os
            api_key = os.getenv('FIREBASE_WEB_API_KEY')
        
        if not api_key:
            print("Warning: Firebase Web API Key not set. Cannot verify passwords.")
            print("Set FIREBASE_WEB_API_KEY environment variable or pass api_key parameter.")
            return None
        
        if not self.project_id:
            print("Warning: Firebase project ID not available.")
            return None
        
        try:
            # Use Firebase REST API to sign in with email/password
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                # Get user details from Admin SDK
                user = auth.get_user(data['localId'])
                return {
                    'uid': user.uid,
                    'email': user.email,
                    'display_name': user.display_name,
                    'id_token': data.get('idToken')
                }
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"Firebase auth error: {error_message}")
                return None
                
        except Exception as e:
            print(f"Error verifying password: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address."""
        try:
            user = auth.get_user_by_email(email)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name
            }
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            print(f"Error getting Firebase user: {e}")
            return None
    
    def get_user_by_uid(self, uid: str) -> Optional[Dict]:
        """Get user by UID."""
        try:
            user = auth.get_user(uid)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name
            }
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            print(f"Error getting Firebase user: {e}")
            return None
    
    def create_custom_token(self, uid: str) -> Optional[str]:
        """Create a custom token for a user."""
        try:
            token = auth.create_custom_token(uid)
            return token.decode('utf-8')
        except Exception as e:
            print(f"Error creating custom token: {e}")
            return None
    
    def verify_id_token(self, id_token: str) -> Optional[Dict]:
        """Verify an ID token and return decoded token."""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Error verifying ID token: {e}")
            return None
    
    def delete_user(self, uid: str) -> bool:
        """Delete a Firebase user."""
        try:
            auth.delete_user(uid)
            return True
        except Exception as e:
            print(f"Error deleting Firebase user: {e}")
            return False
    
    def update_user(self, uid: str, **kwargs) -> Optional[Dict]:
        """Update user properties."""
        try:
            user = auth.update_user(uid, **kwargs)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name
            }
        except Exception as e:
            print(f"Error updating Firebase user: {e}")
            return None
    
    def set_custom_claims(self, uid: str, claims: Dict) -> bool:
        """Set custom claims for a user (e.g., admin status)."""
        try:
            auth.set_custom_user_claims(uid, claims)
            return True
        except Exception as e:
            print(f"Error setting custom claims: {e}")
            return False
    
    def set_admin_claim(self, uid: str, is_admin: bool = True, permissions: list = None) -> bool:
        """Set admin custom claim for a user."""
        claims = {'admin': is_admin}
        if permissions:
            claims['permissions'] = permissions
        return self.set_custom_claims(uid, claims)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.
        Returns (is_valid, error_message)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        return True, None
