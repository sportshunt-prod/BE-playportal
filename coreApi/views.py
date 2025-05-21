from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from sportshunt.utils import login_required_api
from rest_framework import status
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import logout
from django.conf import settings
from django.utils import timezone
from sportshunt.utils import get_user_from_token
from .models import *
from organizationApi.models import Tournament, Category
from .serializers import TournamentListSerializer, UserProfileSerializer, TournamentDetailSerializer, CategorySerializer


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
    token = req.COOKIES.get('jwt_token')
    if token:
        if user := get_user_from_token(token):

            user = User.objects.get(id=user)
            return Response({
                'isAuthenticated': True,
                'user': {
                    'id': user.id,
                    'name': user.username,
                    'email': user.email,
                    'is_org': user.is_organizer
                }
            })
    return Response({
        'isAuthenticated': False
    })

def login_view(req):
    """
    Redirect user to Auth0 login page.
    
    This view redirects the user to Auth0's authentication page to initiate
    the OAuth login flow.
    
    HTTP Method: GET
    
    Returns:
        HttpResponseRedirect: Redirects to Auth0 login page
    """
    return HttpResponseRedirect(reverse('social:begin', args=['auth0']))

def logout_view(req):
    """
    Log out the user and redirect to Auth0 logout page.
    
    This view logs out the user from the application and redirects to Auth0's
    logout endpoint to complete the logout process.
    
    HTTP Method: GET
    
    Returns:
        HttpResponseRedirect: Redirects to Auth0 logout page
    """
    logout(req)
    
    domain = settings.SOCIAL_AUTH_AUTH0_DOMAIN
    client_id = settings.SOCIAL_AUTH_AUTH0_KEY
    return_to = req.build_absolute_uri(reverse('core:logout_handler'))

    return HttpResponseRedirect(f"https://{domain}/v2/logout?client_id={client_id}&returnTo={return_to}")

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
    ).order_by('start_date')[:4]
    
    # Get past tournaments
    past_tournaments = Tournament.objects.filter(
        end_date__lt=current_date
    ).order_by('-end_date')[:4]
    
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
    print(request.user)
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
    tournament = get_object_or_404(Tournament, id=tournament_id)
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