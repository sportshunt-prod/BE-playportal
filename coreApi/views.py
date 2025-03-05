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
    token = req.COOKIES.get('jwt_token')
    if token:
        if user := get_user_from_token(token):

            user = User.objects.get(id=user)
            return Response({
                'isAuthenticated': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
    
    return Response({
        'isAuthenticated': False
    })

def login_view(req):
    return HttpResponseRedirect(reverse('social:begin', args=['auth0']))

def logout_view(req):
    logout(req)
    
    domain = settings.SOCIAL_AUTH_AUTH0_DOMAIN
    client_id = settings.SOCIAL_AUTH_AUTH0_KEY
    return_to = req.build_absolute_uri(reverse('core:logout_handler'))

    return HttpResponseRedirect(f"https://{domain}/v2/logout?client_id={client_id}&returnTo={return_to}")

@api_view(['GET'])
def tournament_list(request):
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
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
def tournament_detail_api(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    serializer = TournamentDetailSerializer(tournament)
    return Response(serializer.data)

@api_view(['GET'])
def category_detail_api(request, tournament_id, category_id):
    category = get_object_or_404(Category, id=category_id, tournament_id=tournament_id)
    serializer = CategorySerializer(category)
    return Response(serializer.data)