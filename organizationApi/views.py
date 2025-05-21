from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from sportshunt.utils import *
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import Organization, Category, Team, Match, SetScore, SimpleScore
from coreApi.models import User
from sportshunt.utils import get_user_from_token
from django.db import transaction
from .utils import KoGen, ScoreManager
import math
import logging

logger = logging.getLogger(__name__)

# Create your views here.

# validate org user
@api_view(['GET'])
def index(req):
    """
    Validate organization user authentication.
    
    This endpoint verifies if a user is authenticated and checks if they are an organizer.
    
    HTTP Method: GET
    
    Returns:
        Response: JSON containing authentication status and user details.
        If authenticated, includes:
        - isAuthenticated: True
        - user: User details (id, name, email, is_org)
        - organization: Organization details if user is an organizer
        
        If not authenticated:
        - isAuthenticated: False
    """
    token = req.COOKIES.get('jwt_token')
    print(token)
    if token:
        print('token')
        if user := get_user_from_token(token):
            print(user)
            user = User.objects.get(id=user)
            print(user)
            response_data = {
                'isAuthenticated': True,
                'user': {
                    'id': user.id,
                    'name': user.username,
                    'email': user.email,
                    'is_org': user.is_organizer,
                },
                'organization': None
            }
            if user.is_organizer:
                org = Organization.objects.filter(admin=user).first()
                if org:
                    response_data['organization'] = {
                        'id': org.id,
                        'name': org.name,
                    }
                print(response_data)
            return Response(response_data)
    return Response({
        'isAuthenticated': False
    })


# create organization
@api_view(['POST'])
@organizer_required_api
def create_organization(request, user=None):
    """
    Create a new organization.
    
    This endpoint allows an authenticated organizer to create a new organization.
    
    HTTP Method: POST
    
    Request Body:
        - Organization data as defined in OrganizationSerializer
    ex. 
    {
    "name": "uhh",
    "mail": "yo@sh.in",
    "ph_number": "1234567890"
    
    }
    
    Returns:
        Response: JSON containing the created organization data with status 201
        or error details with status 400 if the request is invalid.
    """
    # Create the organization
    serializer = OrganizationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(admin=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@organizer_required_api 
def create_tournament(request):
    """
    Create a new tournament.
    
    This endpoint allows an authenticated organizer to create a new tournament.
    
    HTTP Method: POST
    
    Request Body:
        - Tournament data as defined in TournamentSerializer
    ex.
    {
    "name": "uhh tournamenr",
    "details":"wfawf",
    "organization": 2,
    "start_date": "2025-05-15",
    "end_date": "2025-05-15",
    "venue_address":"fwafa",
    "ph_number": "1234567890"
    }
    
    
    Returns:
        Response: JSON containing the created tournament data with status 201
        or error details with status 400 if the request is invalid.
    """
    # Create the tournament
    serializer = TournamentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@organizer_required_api
def create_category(request, tournament_id):
    """
    Create a new category for a specific tournament.
    
    This endpoint allows an authenticated organizer to create a new category
    within an existing tournament.
    
    HTTP Method: POST
    
    URL Parameters:
        - tournament_id: ID of the tournament to add the category to
    
    Request Body:
        - Category data as defined in CategorySerializer
    ex.
    {
    "name": "U19GS",
    "details": "yggg",
    "price": "500",
    "tournament_id": 2
    }
    
    Returns:
        Response: JSON containing the created category data with status 201
        or error details with status 400 if the request is invalid.
    """
    # Create the category
    serializer = CategorySerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        category = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@organizer_required_api
def toggle_registration(request, tournament_id, category_id):
    """
    Toggle registration status for a category.
    
    This endpoint allows an authenticated organizer to open or close the registration
    for a specific category in a tournament. Registration cannot be closed if no teams
    are registered.
    
    HTTP Method: POST
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category to toggle registration for
    
    Returns:
        Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - new_status: New registration status (True/False)
        - status_text: Human-readable status text
        
        Or error details with appropriate status code.
    """
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
    
    This endpoint allows an authenticated organizer to register a new team
    for a specific category in a tournament.
    
    HTTP Method: POST
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category to register the team for
    
    Request Body:
        - Team data as defined in TeamSerializer
    {
    "name": "offline team 1"
    }
    
    Returns:
        Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - team: Details of the created team (id, name, category)
        
        Or error details with appropriate status code.
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
    
    This endpoint allows an authenticated organizer to create a fixture
    for a specific category in a tournament. Supports two fixture types:
    Knockout (KO) and Round Robin (RR).
    
    HTTP Method: POST
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category to create a fixture for
    
    Request Body:
        - Fixture data as defined in FixtureSerializer
        - Must include 'fixtureType' field ('KO' or 'RR')
    ex.
    {
    "fixtureType": "KO"
    }
    Returns:
        Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - fixture: Details of the created fixture (id, type, category)
        
        Or error details with appropriate status code.
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


@api_view(['GET'])
@organizer_required_api
def org_dashboard(request):
    """
    Get organization dashboard data.
    
    This endpoint provides dashboard data for an authenticated organizer,
    including upcoming and past tournaments organized by the user.
    
    HTTP Method: GET
    
    Returns:
        Response: JSON containing:
        - upcoming_tournaments: List of tournaments with future start dates
        - past_tournaments: List of tournaments with past end dates
        
        Or error details with status 500 if an error occurs.
    """
    # add needed data to org dashboard if needed
    response = {
        "upcoming_tournaments": [],
        "past_tournaments": [],
    }
    try:
        # Get organization where user is admin
        user_orgs = Organization.objects.filter(admin=request.user)
        
        # Get current date
        current_date = datetime.now().date()
        
        # Get upcoming tournaments (start date is in the future)
        upcoming = Tournament.objects.filter(
            organization__in=user_orgs,
            start_date__gte=current_date
        )
        
        # Get past tournaments (end date is in the past)
        past = Tournament.objects.filter(
            organization__in=user_orgs,
            end_date__lt=current_date
        )
        
        # Serialize both sets of tournaments
        upcoming_serializer = TournamentSerializer(upcoming, many=True)
        past_serializer = TournamentSerializer(past, many=True)
        
        response["upcoming_tournaments"] = upcoming_serializer.data
        response["past_tournaments"] = past_serializer.data
        
        return Response(response)
    
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@organizer_required_api
def create_ko_matches(request, tournament_id, category_id):
    """
    Create knockout matches for a specific category in a tournament.
    
    This endpoint creates knockout matches based on provided team pairings.
    
    HTTP Method: POST
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category to create matches for
    
    Request Body:
        {
            "matches": [
                {"team_1": 1, "team_2": 2},
                {"team_1": 3, "team_2": "BYE"},
                ...
            ],
            "no_sets": 3,  # Optional, for sports with sets
            "points_win": 15  # Optional, for sports with sets
        }
    
    Returns:
        Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - message: Success message
        
        Or error details with appropriate status code.
    """
    try:
        # Validate category exists and is knockout type
        category_instance = Category.objects.get(id=category_id, tournament_id=tournament_id)
        if not hasattr(category_instance, 'fixture') or category_instance.fixture.fixtureType != "KO":
            return Response({'error': 'Category is not knockout type'}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize KO generator based on sport type
        if category_instance.tournament.sport.scoring_type == "sets":
            no_sets = int(request.data.get("no_sets", 3))
            points_win = int(request.data.get("points_win", 15))
            ko_gen = KoGen(category_instance, request.data, no_sets, points_win)
        else:
            ko_gen = KoGen(category_instance, request.data)
        
        # Create matches
        result = ko_gen.create_matches()
        
        # Check for errors
        if isinstance(result, dict):
            if 'error' in result:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            if 'errors' in result:
                return Response({'errors': result['errors']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True, 
            'message': 'Knockout matches created successfully'
        })

    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found or does not belong to the specified tournament'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@organizer_required_api
def schedule_match(request, tournament_id, category_id):
    """
    Schedule a match from a fixture's bracket matches.
    
    This endpoint allows scheduling a match from either KO or RR fixtures.
    The match is moved from bracket_matches to scheduled_matches.
    
    HTTP Method: POST
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category containing the match
    
    Request Body:
        {
            "match_id": 1  # ID of the match to be scheduled
        }
    
    Returns:
        Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - message: Success or error message
        
        Or error details with appropriate status code.
    """
    try:
        # Get category and verify fixture exists
        category_instance = Category.objects.get(id=category_id, tournament_id=tournament_id)
        fixture = category_instance.fixture
        
        if not fixture:
            return Response(
                {'error': 'Fixture not created yet'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get match_id from request data
        match_id = int(request.data.get('match_id'))
        
        # Handle KO fixture type
        if category_instance.fixture.fixtureType == 'KO':
            ko_instance = fixture.content_object
            bracket_matches = ko_instance.bracket_matches.values_list('id', flat=True)
            
            if match_id not in bracket_matches:
                return Response(
                    {'error': 'Match not found in bracket matches'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                with transaction.atomic():
                    match_instance = Match.objects.get(id=match_id)
                    
                    # Schedule the match
                    fixture.scheduled_matches.add(match_instance)
                    ko_instance.bracket_matches.remove(match_instance)
                    
                    # Save changes
                    fixture.save()
                    ko_instance.save()
                    
                return Response({
                    'success': True,
                    'message': 'Match scheduled successfully',
                    'match': {
                        'id': match_instance.id,
                        'team1': match_instance.team1.name if match_instance.team1 else 'BYE',
                        'team2': match_instance.team2.name if match_instance.team2 else 'BYE'
                    }
                })
            
            except Match.DoesNotExist:
                return Response(
                    {'error': 'Match not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Handle RR fixture type
        elif category_instance.fixture.fixtureType == 'RR':
            rr_instance = fixture.content_object
            bracket_matches = rr_instance.bracket_matches.values_list('id', flat=True)
            
            if match_id not in bracket_matches:
                return Response(
                    {'error': 'Match not found in round matches'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                with transaction.atomic():
                    match_instance = Match.objects.get(id=match_id)
                    
                    # Schedule the match
                    fixture.scheduled_matches.add(match_instance)
                    rr_instance.bracket_matches.remove(match_instance)
                    
                    # Save changes
                    fixture.save()
                    rr_instance.save()
                    
                return Response({
                    'success': True,
                    'message': 'Match scheduled successfully',
                    'match': {
                        'id': match_instance.id,
                        'team1': match_instance.team1.name if match_instance.team1 else 'BYE',
                        'team2': match_instance.team2.name if match_instance.team2 else 'BYE'
                    }
                })
            
            except Match.DoesNotExist:
                return Response(
                    {'error': 'Match not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        else:
            return Response(
                {'error': 'Unsupported fixture type'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found or does not belong to the specified tournament'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response(
            {'error': 'Invalid match ID provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error scheduling match: {str(e)}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@organizer_required_api
def update_score(request, tournament_id, category_id):
    """
    Update the score for a match.
    
    This endpoint handles score updates for both set-based and simple scoring matches.
    For set-based scoring: Updates individual set scores until match completion.
    For simple scoring: Updates match score and can finish the match.
    
    HTTP Method: POST
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category containing the match
    
    Request Body:
        {
            "match_id": 1,           # ID of the match to update
            "action": "increment",   # "increment", "decrement", or "finish"
            "team_id": 1            # ID of team to update score (not needed for "finish")
        }
    
    Returns:
        Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - message: Success or error message
        
        Or error details with appropriate status code.
    """
    try:
        # Validate category and fixture
        category_instance = Category.objects.get(id=category_id, tournament_id=tournament_id)
        if not hasattr(category_instance, 'fixture') or not category_instance.fixture:
            return Response(
                {'error': 'Fixture not created yet'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get match ID and validate action
        match_id = int(request.data.get('match_id'))
        action = request.data.get('action')
        
        if action not in ['increment', 'decrement', 'finish']:
            return Response(
                {'error': 'Invalid action. Must be increment, decrement, or finish'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get match instance
        try:
            match_instance = Match.objects.get(id=match_id)
        except Match.DoesNotExist:
            return Response(
                {'error': 'Match not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Process score update
        score_manager = ScoreManager(request, match_instance, category_instance)
        result = score_manager.process_score_update(action)
        
        return Response(
            result, 
            status=status.HTTP_200_OK if result.get('success', False) 
            else status.HTTP_400_BAD_REQUEST
        )

    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found or does not belong to the specified tournament'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error updating match score: {str(e)}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


