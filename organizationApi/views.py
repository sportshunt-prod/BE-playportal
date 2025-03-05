from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from sportshunt.utils import *
from rest_framework.response import Response
from rest_framework import status
from organizationApi.serializers import *
from organizationApi.models import Organization
# Create your views here.

# create organization
@api_view(['POST'])
@organizer_required_api
def create_organization(request, user=None):
    # Create the organization
    serializer = OrganizationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@organizer_required_api 
def create_tournament(request):
    # Create the tournament
    serializer = TournamentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@organizer_required_api
def create_category(request, tournament_id):
    # Create the category
    serializer = CategorySerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        category = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)