from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from sportshunt.utils import login_required_api, get_user_from_token
from sportshunt.utils.authentication import get_auth_response
from sportshunt.utils.google_auth import verify_google_token, get_or_create_google_user
from rest_framework import status
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from .models import *
from organizationApi.models import Tournament, Category
from .serializers import (
    TournamentListSerializer, UserProfileSerializer, TournamentDetailSerializer, 
    CategorySerializer, RegisterSerializer, LoginSerializer, GoogleAuthSerializer
)
import jwt
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def index(req):
    """
    Check user authentication status.
    
    This endpoint verifies if a user is authenticated by checking their JWT token.
    
    HTTP Method: GET
    
    Returns:
        Response: JSON containing authentication status and user details.
        If authenticated, includes:
        - isAuthenticated: True
        - user: User details (id, name, email, is_org)
        
        If not authenticated:
        - isAuthenticated: False
    """
    return get_auth_response(req, include_organization=False)


@api_view(['POST'])
def register_api(req):
    """
    Register new user with email/password.
    
    This endpoint creates a new user account with email and password,
    then generates a JWT token for immediate authentication.
    
    HTTP Method: POST
    
    Body:
        - email: User's email address
        - username: Desired username
        - password: Password (min 8 characters)
        - password_confirm: Password confirmation
    
    Returns:
        Response: JSON containing registration status, user details, and JWT token
    """
    serializer = RegisterSerializer(data=req.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT
        payload = {
            'user_id': user.id,
            'exp': datetime.now() + timedelta(days=30)
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
        
        logger.info(f"User registered: {user.username}")
        
        return Response({
            'message': 'Registration successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_organizer': user.is_organizer
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_api(req):
    """
    Login with email/password.
    
    This endpoint authenticates a user with email and password credentials,
    then generates a JWT token for API authorization.
    
    HTTP Method: POST
    
    Body:
        - email: User's email address
        - password: User's password
    
    Returns:
        Response: JSON containing login status, user details, and JWT token
    """
    serializer = LoginSerializer(data=req.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                # Generate JWT
                payload = {
                    'user_id': user.id,
                    'exp': datetime.now() + timedelta(days=30)
                }
                token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
                
                logger.info(f"User logged in: {user.username}")
                
                return Response({
                    'message': 'Login successful',
                    'token': token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_organizer': user.is_organizer
                    }
                })
            else:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def google_auth_api(req):
    """
    Login/register with Google OAuth.
    
    This endpoint authenticates or creates a user using Google OAuth credentials,
    then generates a JWT token for API authorization.
    
    HTTP Method: POST
    
    Body:
        - credential: Google ID token from Google Sign-In
    
    Returns:
        Response: JSON containing authentication status, user details, and JWT token
    """
    serializer = GoogleAuthSerializer(data=req.data)
    if serializer.is_valid():
        credential = serializer.validated_data['credential']
        
        google_info = verify_google_token(credential)
        if not google_info:
            return Response(
                {'error': 'Invalid Google token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = get_or_create_google_user(google_info)
        
        # Generate JWT
        payload = {
            'user_id': user.id,
            'exp': datetime.now() + timedelta(days=30)
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
        
        logger.info(f"User authenticated via Google: {user.username}")
        
        return Response({
            'message': 'Google authentication successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_organizer': user.is_organizer
            }
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_view(req):
    """
    Logout user.
    
    With Bearer token authentication, logout is handled client-side by
    removing the token from storage. This endpoint is kept for consistency
    and can be used for logging purposes.
    
    HTTP Method: POST
    
    Returns:
        Response: JSON confirming logout
    """
    logger.info("User logged out")
    return Response({'message': 'Logout successful'})

@api_view(['GET'])
def tournament_list(request):
    """
    Get a list of upcoming and past tournaments.
    
    This endpoint provides lists of upcoming tournaments (start date in the future)
    and past tournaments (end date in the past), limited to 4 of each.
    
    HTTP Method: GET
    
    Returns:
        Response: JSON containing:
        - upcoming_tournaments: List of tournaments with future start dates (max 4)
        - past_tournaments: List of tournaments with past end dates (max 4)
    """
    current_date = timezone.now().date()
      # Get upcoming tournaments
    upcoming_tournaments = Tournament.objects.filter(
        start_date__gt=current_date
    ).select_related('organization', 'sport').order_by('start_date')[:4]
    
    # Get past tournaments
    past_tournaments = Tournament.objects.filter(
        end_date__lt=current_date
    ).select_related('organization', 'sport').order_by('-end_date')[:4]
    
    # Serialize the data
    upcoming_serializer = TournamentListSerializer(upcoming_tournaments, many=True)
    past_serializer = TournamentListSerializer(past_tournaments, many=True)
    
    return Response({
        'upcoming_tournaments': upcoming_serializer.data,
        'past_tournaments': past_serializer.data
    })

@api_view(['GET'])
@login_required_api
def profile_api(request):
    """
    Get the profile of the authenticated user.
    
    This endpoint returns the profile information of the currently authenticated user.
    Requires authentication.
    
    HTTP Method: GET
      Returns:
        Response: JSON containing the user's profile information as defined in
        UserProfileSerializer (username, email, is_organizer, etc.)
    """
    logger.debug(f"Fetching profile for user: {request.user.username} (ID: {request.user.id})")
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
def tournament_detail_api(request, tournament_id):
    """
    Get detailed information about a specific tournament.
    
    This endpoint provides detailed information about a tournament, including
    its categories, organization, dates, location, etc.
    
    HTTP Method: GET
    
    URL Parameters:
        - tournament_id: ID of the tournament to retrieve
    
    Returns:
        Response: JSON containing detailed tournament information as defined in
        TournamentDetailSerializer
        
        Or 404 status if the tournament doesn't exist
    """
    tournament = get_object_or_404(
        Tournament.objects.select_related('organization', 'sport').prefetch_related('categories'), 
        id=tournament_id
    )
    serializer = TournamentDetailSerializer(tournament)
    return Response(serializer.data)

@api_view(['GET'])
def category_detail_api(request, tournament_id, category_id):
    """
    Get detailed information about a specific category in a tournament.
    
    This endpoint provides detailed information about a category within a tournament,
    including its name, teams, fixtures, etc.
    
    HTTP Method: GET
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category to retrieve
    
    Returns:
        Response: JSON containing detailed category information as defined in
        CategorySerializer
        
        Or 404 status if the category or tournament doesn't exist
    """
    category = get_object_or_404(Category, id=category_id, tournament_id=tournament_id)
    serializer = CategorySerializer(category)
    return Response(serializer.data)