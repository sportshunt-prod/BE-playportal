"""
Core utility functions and decorators for the SportsHunt application.

This module contains authentication decorators and JWT handling utilities.
"""

from functools import wraps
from coreApi.models import User
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponseRedirect
import jwt
from datetime import datetime, timedelta
from django.conf import settings
import logging

from organizationApi.models import Tournament, Category

logger = logging.getLogger(__name__)


def login_required_api(f):
    @wraps(f)
    def decorated_function(req,  *args, **kwargs):
        # Get token from Authorization header
        auth_header = req.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            logger.debug("Missing or invalid Authorization header")
            return Response(
                {"error": "Authorization header required. Format: Bearer <token>"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Extract token (remove 'Bearer ' prefix)
        token = auth_header[7:]
        
        # Development mode - remove in production
        # if True: # Change to DEV mode if needed
        #     user_instance = User.objects.get(id=3)
        #     req.user = user_instance
        #     return f(req, *args, **kwargs)
        
        if user_id := get_user_from_token(token):
            try:
                user_instance = User.objects.get(id=user_id)
                req.user = user_instance
                logger.debug(f"User authenticated: {user_instance.username}")
                return f(req, *args, **kwargs)
            except User.DoesNotExist:
                logger.warning(f"User with ID {user_id} not found")
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        logger.debug("Invalid or expired token")
        return Response(
            {"error": "Invalid or expired token"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return decorated_function


def organizer_required_api(f):
    @wraps(f)
    def decorated_function(req, *args, **kwargs):
        
        # if True:
        #     req.user = User.objects.get(id=3)
        #     return f(req, *args, **kwargs)
        
        # Get token from Authorization header
        auth_header = req.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            logger.debug("Missing or invalid Authorization header")
            return Response(
                {"error": "Authorization header required. Format: Bearer <token>"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Extract token (remove 'Bearer ' prefix)
        token = auth_header[7:]
        user_id = get_user_from_token(token)
        
        if not user_id:
            logger.debug("Invalid or expired token")
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            user_instance = User.objects.get(id=user_id)
            req.user = user_instance
            
            if not user_instance.is_organizer:
                logger.warning(f"Non-organizer user {user_instance.username} attempted to access organizer endpoint")
                return Response(
                    {"error": "Only organizers can access this endpoint"},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Check tournament access if tournament_id is provided
            if 'tournament_id' in kwargs:
                tournament_id = kwargs['tournament_id']
                try:
                    tournament_instance = Tournament.objects.get(id=tournament_id)
                    if tournament_instance.organization.admin != user_instance:
                        logger.warning(f"User {user_instance.username} attempted to access tournament {tournament_id} without permission")
                        return Response(
                            {"error": "You don't have permission to manage this tournament"},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Tournament.DoesNotExist:
                    logger.error(f"Tournament {tournament_id} not found")
                    return Response(
                        {"error": "Tournament not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
            # Check category access if category_id is provided
            if 'category_id' in kwargs:
                category_id = kwargs['category_id']
                try:
                    category_instance = Category.objects.get(id=category_id)
                    if category_instance.tournament.organization.admin != user_instance:
                        logger.warning(f"User {user_instance.username} attempted to access category {category_id} without permission")
                        return Response(
                            {"error": "You don't have permission to manage this category"},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Category.DoesNotExist:
                    logger.error(f"Category {category_id} not found")
                    return Response(
                        {"error": "Category not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
            logger.debug(f"Organizer {user_instance.username} authorized for endpoint")
            return f(req, *args, **kwargs)
            
        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    return decorated_function


def get_user_from_token(token):
    """
    Extract user ID from JWT token.
    
    Args:
        token (str): JWT token string
        
    Returns:
        int|None: User ID if token is valid, None otherwise
    """
    try:
        # Decode the JWT token with leeway for clock skew
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'], leeway=10)
        user_id = payload.get('user_id')
        return user_id
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.debug("Invalid JWT token")
        return None
    except jwt.ImmatureSignatureError:
        logger.debug("JWT token not yet valid (iat)")
        return None
    

def logout_handler(req):
    """
    Handle user logout.
    
    With Bearer token authentication, logout is handled client-side by
    removing the token from storage. This handler redirects to the frontend.
    """
    frontend_url = settings.FRONTEND_URL[0]
    response = HttpResponseRedirect(f"{frontend_url}")
    
    logger.info("User logged out successfully")
    return response
