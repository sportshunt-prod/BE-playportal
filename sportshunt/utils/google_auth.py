"""
Google OAuth authentication utilities for the SportsHunt application.

This module contains functions for verifying Google ID tokens and managing
user authentication via Google OAuth.
"""

from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from coreApi.models import User
import logging

logger = logging.getLogger(__name__)


def verify_google_token(credential):
    """
    Verify Google ID token and return user info.
    
    Args:
        credential (str): Google ID token string
        
    Returns:
        dict|None: User information if token is valid, None otherwise
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            credential, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer')
            
        return {
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'google_id': idinfo['sub'],
            'email_verified': idinfo.get('email_verified', False)
        }
    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Google token verification: {e}")
        return None


def get_or_create_google_user(google_info):
    """
    Get or create user from Google profile.
    
    Args:
        google_info (dict): Google user information from verify_google_token
        
    Returns:
        User: User instance
    """
    email = google_info['email']
    
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],
            'first_name': google_info.get('name', '').split()[0] if google_info.get('name') else '',
        }
    )
    
    if created:
        logger.info(f"New user created via Google: {email}")
    else:
        logger.info(f"Existing user authenticated via Google: {email}")
    
    return user

