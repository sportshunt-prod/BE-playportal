from functools import wraps
from coreApi.models import User
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
import jwt
from datetime import datetime, timedelta
from django.conf import settings

from organizationApi.models import *


def login_required_api(f):
    @wraps(f)
    def decorated_function(req,  *args, **kwargs):
        token = req.COOKIES.get('jwt_token')
        
        if True: # Change to DEV mode if needed
            user_instance = User.objects.get(id=2)
            req.user = user_instance
            return f(req, *args, **kwargs)
        
        if token:
            if user := get_user_from_token(token):
                try:
                    user_instance = User.objects.get(id=user)
                    req.user = user_instance
                    return f(req, *args, **kwargs)
                except User.DoesNotExist:
                    return Response(
                        {"error": "User not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
        
        # user_instance = User.objects.get(id=1)
        # print(user_instance)
        # return f(req, user=user_instance, *args, **kwargs)
                
        return Response(
            {"error": "Unauthorized"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return decorated_function


def organizer_required_api(f):
    @wraps(f)
    def decorated_function(req, *args, **kwargs):
        # token = req.COOKIES.get('jwt_token')
        # if not token:
        #     return Response(
        #         {"error": "Authentication token missing"},
        #         status=status.HTTP_401_UNAUTHORIZED
        #     )
            
        # user_id = get_user_from_token(token)
        # if not user_id:
        #     return Response(
        #         {"error": "Invalid or expired token"},
        #         status=status.HTTP_401_UNAUTHORIZED
        #     )
        user_id = 2 # Hardcoded for testing
        try:
            user_instance = User.objects.get(id=user_id)
            req.user = user_instance
            
            if not user_instance.is_organizer:
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
                        return Response(
                            {"error": "You don't have permission to manage this tournament"},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Tournament.DoesNotExist:
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
                        return Response(
                            {"error": "You don't have permission to manage this category"},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Category.DoesNotExist:
                    return Response(
                        {"error": "Category not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
            return f(req, *args, **kwargs)
            
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    
    return decorated_function


@login_required
def login_handler(req):
    # Generate JWT
    payload = {
        'user_id': req.user.id,
        'exp': datetime.now() + timedelta(days=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
    
    # Redirect to frontend with token
    frontend_url = settings.FRONTEND_URL[0]
    response = HttpResponseRedirect(f"{frontend_url}")
    
    # Set JWT as cookie
    response.set_cookie(    
        'jwt_token', 
        token,
        httponly=True, 
        secure=True,
        samesite='None' # Set 'Lax' in production (dk doubt hv to check)
    )
    
    return response

def get_user_from_token(token):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('user_id')
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
def logout_handler(req):
    frontend_url = settings.FRONTEND_URL[0]
    response = HttpResponseRedirect(f"{frontend_url}")
    
    # Remove JWT as cookie
    response.delete_cookie('jwt_token')
    
    return response