from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from sportshunt.utils import *
from rest_framework.response import Response
from rest_framework import status
from organizationApi.serializers import *
from organizationApi.models import Organization, Category, Team
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

@api_view(['POST'])
@organizer_required_api
def toggle_registration(request, tournament_id, category_id):
    try:
        category = Category.objects.get(id=category_id, tournament_id=tournament_id)
        
        # Check if trying to close registration
        if category.registration_status and category.teams.all().count() == 0:
            return Response(
                {'error': 'Cannot close registration - no teams registered'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        category.registration_status = not category.registration_status
        category.save()
        
        return Response({
            'success': True, 
            'new_status': category.registration_status,
            'status_text': category.reg_status
        })
    
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@organizer_required_api
def register_team(request, tournament_id, category_id):
    """
    Register a new team for a specific category in a tournament.
    """
    try:
        # Verify the category exists and belongs to the specified tournament
        category = Category.objects.get(id=category_id, tournament_id=tournament_id)
        
        # Create team data with the specified category
        team_data = request.data.copy()
        team_data['category'] = category_id
        
        serializer = TeamSerializer(data=team_data)
        if serializer.is_valid():
            team = serializer.save()
            return Response({
                'success': True,
                'team': {
                    'id': team.id,
                    'name': team.name,
                    'category': category.name
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Category.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Category not found or does not belong to the specified tournament'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@organizer_required_api
def create_fixture(request, tournament_id, category_id):
    """
    Create a fixture for a specific category in a tournament.
    Supports two fixture types: Knockout (KO) and Round Robin (RR).
    """
    try:
        # Verify the category exists and belongs to the specified tournament
        category = Category.objects.get(id=category_id, tournament_id=tournament_id)
        
        # Check if the category already has a fixture
        # if hasattr(category, 'fixture') and category.fixture:
        #     return Response(
        #         {'error': 'This category already has a fixture'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        
        # Validate and create fixture
        serializer = FixtureSerializer(data=request.data)
        if serializer.is_valid():
            fixture = serializer.create_fixture(category)
            
            response_data = {
                'success': True,
                'fixture': {
                    'id': fixture.id,
                    'type': fixture.fixtureType,
                    'category': category.name
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found or does not belong to the specified tournament'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    except serializers.ValidationError as e:
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


