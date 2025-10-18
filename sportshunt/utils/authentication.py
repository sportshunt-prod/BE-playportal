"""
Shared authentication utilities for the SportsHunt application.

This module contains common authentication logic that can be reused across different views
to eliminate code duplication and improve maintainability.
"""

import logging
from rest_framework.response import Response
from coreApi.models import User
from organizationApi.models import Organization
from sportshunt.utils import get_user_from_token

logger = logging.getLogger(__name__)


def get_auth_response(request, include_organization=False):
    """
    Get authentication response for the current request.
    
    This function checks for JWT token in Authorization header, validates it, and returns
    the appropriate authentication response.
    
    Args:
        request: Django request object
        include_organization (bool): Whether to include organization details for organizers
        
    Returns:
        Response: JSON response containing authentication status and user details
    """
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        logger.debug("No valid Authorization header found")
        return Response({'isAuthenticated': False})
    
    # Extract token (remove 'Bearer ' prefix)
    token = auth_header[7:]
    
    user_id = get_user_from_token(token)
    if not user_id:
        logger.debug("Invalid or expired JWT token")
        return Response({'isAuthenticated': False})
    
    try:
        user = User.objects.get(id=user_id)
        logger.debug(f"Authenticated user: {user.username} (ID: {user.id})")
        
        response_data = {
            'isAuthenticated': True,
            'user': {
                'id': user.id,
                'name': user.username,
                'email': user.email,
                'is_org': user.is_organizer,
            }
        }
        
        if include_organization and user.is_organizer:
            organization = Organization.objects.filter(admin=user).first()
            if organization:
                response_data['organization'] = {
                    'id': organization.id,
                    'name': organization.name,
                }
                logger.debug(f"Included organization details: {organization.name}")
            else:
                response_data['organization'] = None
                logger.warning(f"User {user.username} is marked as organizer but has no organization")
        
        return Response(response_data)
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found in database")
        return Response({'isAuthenticated': False})