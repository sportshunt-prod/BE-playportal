from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from sportshunt.utils import organizer_required_api, login_required_api, get_user_from_token
from sportshunt.utils.authentication import get_auth_response
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import Organization, Category, Team, Match, SetScore, SimpleScore, Court, Tournament
from coreApi.models import User
from django.db import transaction
from .utils import KoGen, ScoreManager, KoGenContentSwap
import math
import logging

logger = logging.getLogger(__name__)


# Helper Functions
def build_match_completion_response(match, available_matches=0, tournament_completed=False, **extra):
    """
    Build standardized match completion response.
    
    Args:
        match: Match instance that was completed
        available_matches: Number of new matches ready for scheduling
        tournament_completed: Boolean indicating if tournament is finished
        **extra: Additional fields to include in response
    
    Returns:
        dict: Standardized response dictionary
    """
    response = {
        'match_completed': match.match_state,
        'winner': match.winner.name if match.winner else None,
        'next_matches_available': available_matches,
        'tournament_completed': tournament_completed
    }
    response.update(extra)
    return response


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
    return get_auth_response(req, include_organization=True)


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
        if category.registration_status and category.teams.count() == 0:
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
    This endpoint provides dashboard data for an authenticated organizer, including organization info and tournaments.
    HTTP Method: GET
    Returns:
        Response: JSON containing:
        - organization: Organization data or null if not found
        - upcoming_tournaments: List of upcoming tournaments (not started yet)
        - ongoing_tournaments: List of currently active tournaments (started but not ended)
        - past_tournaments: List of past tournaments (ended)
    """
    try:
        # Get organization where user is admin
        user_org = Organization.objects.get(admin=request.user)
        if user_org:
            org_data = OrganizationSerializer(user_org).data
            # Get current date
            from datetime import datetime
            current_date = datetime.now().date()
            
            # Upcoming: Tournaments that haven't started yet
            upcoming = user_org.tournaments.filter(start_date__gt=current_date)
            
            # Ongoing: Tournaments currently happening (started but not ended)
            ongoing = user_org.tournaments.filter(start_date__lte=current_date,end_date__gte=current_date)
            # Past: Tournaments that have ended
            past = user_org.tournaments.filter(end_date__lt=current_date)
            
            # Serialize the data
            upcoming_serializer = TournamentSerializer(upcoming, many=True)
            ongoing_serializer = TournamentSerializer(ongoing, many=True)
            past_serializer = TournamentSerializer(past, many=True)
            
            upcoming_tournaments = upcoming_serializer.data
            ongoing_tournaments = ongoing_serializer.data
            past_tournaments = past_serializer.data
        else:
            org_data = None
            upcoming_tournaments = []
            ongoing_tournaments = []
            past_tournaments = []
        
        return Response({
            "organization": org_data,
            "upcoming_tournaments": upcoming_tournaments,
            "ongoing_tournaments": ongoing_tournaments,
            "past_tournaments": past_tournaments,
            "matches_scheduled": []
        })
    except Exception as e:
        return Response({
            "organization": None,
            "upcoming_tournaments": [],
            "ongoing_tournaments": [],
            "past_tournaments": [],
            "matches_scheduled": []
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@organizer_required_api
def create_ko_matches(request, tournament_id, category_id):
    """
    Create knockout matches based on organizer-selected team pairings.
    
    This endpoint creates knockout matches based on user-provided team pairings.
    Organizers decide which teams play against each other.
    
    HTTP Method: POST
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category to create matches for
    
    Request Body:
        {
            "matches": [
                {"team_1": 1, "team_2": 2},
                {"team_1": 3, "team_2": 4},
                {"team_1": 5, "team_2": "BYE"}  # BYE for odd teams
            ],
            "no_sets": 3,  # Required for set-based sports
            "points_win": 15  # Required for set-based sports
        }
    
    Returns:
        Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - message: Success message
        - matches_created: Total number of matches created
        - immediately_schedulable: Number of matches ready for scheduling
        
        Or error details with appropriate status code.
    """
    try:
        # Validate category exists and is knockout type
        category_instance = Category.objects.get(id=category_id, tournament_id=tournament_id)
        if not hasattr(category_instance, 'fixture') or category_instance.fixture.fixtureType != "KO":
            return Response({'error': 'Category is not knockout type'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if matches already exist
        existing_matches = category_instance.fixture.content_object.all_matches.count()
        if existing_matches > 0:
            return Response({'error': 'Matches already created for this category'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate matches data is provided
        if not request.data.get('matches'):
            return Response({'error': 'Match pairings are required. Please provide "matches" array with team pairings.'}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize KO generator based on sport type
        if category_instance.tournament.sport.scoring_type == "sets":
            no_sets = int(request.data.get("no_sets", 3))
            points_win = int(request.data.get("points_win", 15))
            ko_gen = KoGen(category_instance, request.data, no_sets, points_win)
        else:
            ko_gen = KoGen(category_instance, request.data)
        
        # Create complete bracket with user-specified teams
        result = ko_gen.create_complete_bracket_with_teams()
        
        # Check for errors
        if isinstance(result, dict):
            if 'error' in result:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            if 'errors' in result:
                return Response({'errors': result['errors']}, status=status.HTTP_400_BAD_REQUEST)        
        
        # Calculate response metrics
        ko_instance = category_instance.fixture.content_object
        total_matches = ko_instance.all_matches.count()
        schedulable_matches = ko_instance.bracket_matches.count()
        
        return Response({
            'success': True, 
            'message': 'Knockout matches created successfully',
            'matches_created': total_matches,
            'immediately_schedulable': schedulable_matches
        }, status=status.HTTP_201_CREATED)

    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found or does not belong to the specified tournament'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({'error': f'Invalid data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating knockout matches: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@organizer_required_api
def schedule_match(request, tournament_id, category_id):
    """
    Schedule a match from a fixture's bracket matches or get all available matches.
    
    This endpoint allows scheduling a match from either KO or RR fixtures with optional court assignment.
    The match is moved from bracket_matches to scheduled_matches.
    Enhanced with court assignment and auto-queue functionality.
    
    HTTP Method: GET, POST
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category containing the match
    
    GET Request:
        Returns all available matches for scheduling
        - For KO fixtures: Checks if base matches exist, returns error if not created
        - Returns matches that can be scheduled (both teams assigned)
        
    POST Request Body:
        {
            "match_id": 1,     # ID of the match to be scheduled
            "court_id": 2      # (Optional) ID of the court to assign the match to
        }
        
    Auto-Queue Logic (when court_id provided):
        - If court.current_match is NULL → assign as current match
        - If court.current_match exists → add to court.upcoming_matches queue
        - Court automatically manages the queue order
    
    Returns:
        GET Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - fixture_type: Type of fixture (KO/RR)
        - available_matches: List of matches available for scheduling
        - total_matches: Total number of matches in the bracket
        - error: Error message if no matches created yet (KO only)
        - next_step: Guidance for next action if no matches exist
        
        POST Response: JSON containing:
        - success: Boolean indicating if the operation was successful
        - message: Success or error message
        - match: Match details
        - court: Court details (if court_id provided)
        - position: "current" or "queued" (if court_id provided)
        - queue_position: Position in queue if queued (if court_id provided)
        - next_available_matches: Number of matches now available for scheduling
        
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

        # Handle GET request - return all available matches
        if request.method == 'GET':
            
            if fixture.fixtureType == 'KO':
                ko_instance = fixture.content_object
                
                # Check if any matches have been created at all
                total_matches_in_fixture = ko_instance.all_matches.count()
                
                if total_matches_in_fixture == 0:
                    return Response({
                        'success': False,
                        'fixture_type': 'KO',
                        'error': 'Base matches need to be created first',
                        'message': 'No matches have been created for this knockout fixture. Please create the base matches first using the create_ko_matches endpoint.',
                        'available_matches': [],
                        'total_matches': 0,
                        'stage_info': 'Matches not created yet',
                        'next_step': 'Create base matches for the knockout tournament'
                    })
                
                # Get all bracket matches that can be scheduled (have both teams assigned)
                available_matches = ko_instance.bracket_matches.filter(
                    team1__isnull=False, 
                    team2__isnull=False
                ).select_related('team1', 'team2')
                
                matches_data = []
                for match in available_matches:
                    matches_data.append({
                        'id': match.id,
                        'team1': {
                            'id': match.team1.id,
                            'name': match.team1.name
                        },
                        'team2': {
                            'id': match.team2.id,
                            'name': match.team2.name
                        },
                        'stage': match.stage_number,
                        'match_number': match.match_number,
                        'can_schedule': True
                    })
                
                return Response({
                    'success': True,
                    'fixture_type': 'KO',
                    'available_matches': matches_data,
                    'total_matches': ko_instance.bracket_matches.count(),
                    'stage_info': f"Stage {matches_data[0]['stage']}" if matches_data else "No matches available"
                })
                
            elif fixture.fixtureType == 'RR_KO':
                rr_ko_instance = fixture.content_object
                # Get current phase
                current_phase = rr_ko_instance.current_phase
                if current_phase == 'round_robin':
                    try:
                        # Get the round robin instance and its matches
                        rr_phase = rr_ko_instance.round_robin_phase
                        bracket_matches = rr_phase.bracket_matches.all()
                        
                        matches_data = []
                        for match in bracket_matches:
                            match_data = {
                                'id': match.id,
                                'team1': {
                                    'id': match.team1.id,
                                    'name': match.team1.name
                                } if match.team1 else None,
                                'team2': {
                                    'id': match.team2.id,
                                    'name': match.team2.name
                                } if match.team2 else None,
                                'round': getattr(match, 'round_number', 1),
                                'match_number': getattr(match, 'match_number', None),
                                'can_schedule': True,
                                'stage': getattr(match, 'stage_number', None)
                            }
                            matches_data.append(match_data)
                        
                        # Get team info
                        teams_data = []
                        for rr_team in rr_phase.rr_teams.select_related('team').all():
                            teams_data.append({
                                'id': rr_team.team.id,
                                'name': rr_team.team.name,
                                'matches_played': rr_team.matches_played,
                                'matches_won': rr_team.matches_won,
                                'matches_lost': rr_team.matches_lost
                            })
                        
                        # Compile stats
                        stats = {
                            'total_matches': rr_phase.all_matches.count(),
                            'scheduled_matches': fixture.scheduled_matches.count(),
                            'remaining_matches': bracket_matches.count(),
                            'total_teams': len(teams_data)
                        }
                        
                        response_data = {
                            'success': True,
                            'fixture_type': 'RR_KO',
                            'current_phase': current_phase,
                            'available_matches': matches_data,
                            'teams': teams_data,
                            'stats': stats
                        }
                        
                        return Response(response_data, status=status.HTTP_200_OK)
                        
                    except Exception as e:
                        logger.error(f"Error retrieving RR phase matches: {str(e)}")
                        return Response(
                            {'error': f'Error retrieving matches: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                elif current_phase == 'knockout':
                    if not rr_ko_instance.knockout_phase:
                        return Response({
                            'error': 'Knockout phase not initialized yet'
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
                    ko_instance = rr_ko_instance.knockout_phase
                    
                    # Check if any matches have been created at all
                    total_matches_in_fixture = ko_instance.all_matches.count()
                    bracket_matches_count = ko_instance.bracket_matches.count()
                    
                    if total_matches_in_fixture == 0:
                        return Response({
                            'success': False,
                            'fixture_type': 'RR_KO',
                            'current_phase': 'knockout',
                            'error': 'Base matches need to be created first',
                            'message': 'No matches have been created for this knockout fixture.',
                            'available_matches': [],
                            'total_matches': 0,
                            'stage_info': 'Matches not created yet'
                        })
                    
                    # Get all bracket matches that can be scheduled (have both teams assigned)
                    available_matches = ko_instance.bracket_matches.filter(
                        team1__isnull=False, 
                        team2__isnull=False
                    ).select_related('team1', 'team2')
                    
                    matches_data = []
                    for match in available_matches:
                        matches_data.append({
                            'id': match.id,
                            'team1': {
                                'id': match.team1.id,
                                'name': match.team1.name
                            },
                            'team2': {
                                'id': match.team2.id,
                                'name': match.team2.name
                            },
                            'stage': match.stage_number,
                            'match_number': match.match_number,
                            'can_schedule': True
                        })
                    
                    return Response({
                        'success': True,
                        'fixture_type': 'RR_KO',
                        'current_phase': 'knockout',
                        'available_matches': matches_data,
                        'total_matches': ko_instance.bracket_matches.count(),
                        'stage_info': f"Stage {matches_data[0]['stage']}" if matches_data else "No matches available"
                    })
            
            elif fixture.fixtureType == 'RR':
                rr_instance = fixture.content_object
                
                # Get all bracket matches for Round Robin
                available_matches = rr_instance.bracket_matches.select_related('team1', 'team2')
                
                matches_data = []
                for match in available_matches:
                    matches_data.append({
                        'id': match.id,
                        'team1': {
                            'id': match.team1.id,
                            'name': match.team1.name
                        },
                        'team2': {
                            'id': match.team2.id,
                            'name': match.team2.name
                        },
                        'round': getattr(match, 'round_number', 1),
                        'can_schedule': True
                    })
                
                return Response({
                    'success': True,
                    'fixture_type': 'RR',
                    'available_matches': matches_data,
                    'total_matches': rr_instance.bracket_matches.count()
                })
            
            else:
                return Response(
                    {'error': 'Unsupported fixture type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Handle POST request - schedule a match
        # Get match_id and court_id from request data
        match_id = request.data.get('match_id')
        
        # Validate match_id is provided
        if not match_id:
            return Response(
                {'error': 'match_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        court_id = request.data.get('court_id')  # NEW: Court assignment parameter
        
        # NEW: Court assignment and validation
        court_instance = None
        court_position = None
        queue_position = None
        
        if court_id:
            try:
                court_instance = Court.objects.get(id=court_id, tournament_id=tournament_id)
            except Court.DoesNotExist:
                return Response(
                    {'error': 'Court not found or does not belong to this tournament'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Handle KO fixture type
        if category_instance.fixture.fixtureType == 'KO':
            ko_instance = fixture.content_object
            bracket_matches = ko_instance.bracket_matches.values_list('id', flat=True)
            
            if match_id not in bracket_matches:
                return Response(
                    {'error': 'Match not found in available bracket matches'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                with transaction.atomic():
                    match_instance = Match.objects.get(id=match_id)
                    
                    # Enhanced validation for complete bracket mode
                    if not match_instance.team1 or not match_instance.team2:
                        return Response(
                            {'error': 'Match cannot be scheduled - both teams must be assigned'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # NEW: Auto-queue logic for court assignment
                    if court_instance:
                        if court_instance.current_match is None:
                            # Court is available - assign as current match
                            court_instance.current_match = match_instance
                            court_position = "current"
                            queue_position = None
                        else:
                            # Court is occupied - add to upcoming queue
                            court_instance.upcoming_matches.add(match_instance)
                            court_position = "queued"
                            queue_position = court_instance.upcoming_matches.count()
                        
                        court_instance.save()
                    
                    # Schedule the match
                    fixture.scheduled_matches.add(match_instance)
                    ko_instance.bracket_matches.remove(match_instance)
                    
                    # Save changes
                    fixture.save()
                    ko_instance.save()
                    
                    # Calculate remaining available matches
                    remaining_matches = ko_instance.bracket_matches.filter(
                        team1__isnull=False, 
                        team2__isnull=False
                    ).count()
                    
                # Enhanced response with court information
                response_data = {
                    'success': True,
                    'message': 'Match scheduled successfully',
                    'match': {
                        'id': match_instance.id,
                        'team1': match_instance.team1.name if match_instance.team1 else 'BYE',
                        'team2': match_instance.team2.name if match_instance.team2 else 'BYE',
                        'stage': match_instance.stage_number,
                        'match_number': match_instance.match_number
                    },
                    'next_available_matches': remaining_matches
                }
                
                # NEW: Add court information to response if court was assigned
                if court_instance:
                    response_data['court'] = {
                        'id': court_instance.id,
                        'name': court_instance.name
                    }
                    response_data['position'] = court_position
                    response_data['queue_position'] = queue_position
                    
                    if court_position == "current":
                        response_data['message'] = f"Match scheduled successfully and assigned to {court_instance.name}"
                    else:
                        response_data['message'] = f"Match scheduled and queued for {court_instance.name} (position {queue_position})"
                
                return Response(response_data)
            
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
                    
                    # NEW: Auto-queue logic for court assignment (same as KO)
                    if court_instance:
                        if court_instance.current_match is None:
                            # Court is available - assign as current match
                            court_instance.current_match = match_instance
                            court_position = "current"
                            queue_position = None
                        else:
                            # Court is occupied - add to upcoming queue
                            court_instance.upcoming_matches.add(match_instance)
                            court_position = "queued"
                            queue_position = court_instance.upcoming_matches.count()
                        
                        court_instance.save()
                    
                    # Schedule the match
                    fixture.scheduled_matches.add(match_instance)
                    rr_instance.bracket_matches.remove(match_instance)
                    
                    # Save changes
                    fixture.save()
                    rr_instance.save()
                    
                    # Calculate remaining matches for consistency
                    remaining_matches = rr_instance.bracket_matches.count()
                    
                # Enhanced response with court information
                response_data = {
                    'success': True,
                    'message': 'Match scheduled successfully',
                    'match': {
                        'id': match_instance.id,
                        'team1': match_instance.team1.name if match_instance.team1 else 'BYE',
                        'team2': match_instance.team2.name if match_instance.team2 else 'BYE',
                        'round': getattr(match_instance, 'round_number', 1)
                    },
                    'next_available_matches': remaining_matches
                }
                
                # NEW: Add court information to response if court was assigned
                if court_instance:
                    response_data['court'] = {
                        'id': court_instance.id,
                        'name': court_instance.name
                    }
                    response_data['position'] = court_position
                    response_data['queue_position'] = queue_position
                    
                    if court_position == "current":
                        response_data['message'] = f"Match scheduled successfully and assigned to {court_instance.name}"
                    else:
                        response_data['message'] = f"Match scheduled and queued for {court_instance.name} (position {queue_position})"
                
                return Response(response_data)
            
            except Match.DoesNotExist:
                return Response(
                    {'error': 'Match not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Handle RR_KO fixture type
        elif category_instance.fixture.fixtureType == 'RR_KO':
            rr_ko_instance = fixture.content_object
            current_phase = rr_ko_instance.current_phase
            
            # Route to appropriate phase handler
            if current_phase == 'round_robin':
                # Handle Round Robin phase scheduling
                rr_phase = rr_ko_instance.round_robin_phase
                bracket_matches = rr_phase.bracket_matches.values_list('id', flat=True)
                
                if match_id not in bracket_matches:
                    return Response(
                        {'error': 'Match not found in round robin matches'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    with transaction.atomic():
                        match_instance = Match.objects.get(id=match_id)
                        
                        # Auto-queue logic for court assignment
                        if court_instance:
                            if court_instance.current_match is None:
                                court_instance.current_match = match_instance
                                court_position = "current"
                                queue_position = None
                            else:
                                court_instance.upcoming_matches.add(match_instance)
                                court_position = "queued"
                                queue_position = court_instance.upcoming_matches.count()
                            
                            court_instance.save()
                        
                        # Schedule the match
                        fixture.scheduled_matches.add(match_instance)
                        rr_phase.bracket_matches.remove(match_instance)
                        
                        # Save changes
                        fixture.save()
                        rr_phase.save()
                        
                        # Calculate remaining matches
                        remaining_matches = rr_phase.bracket_matches.count()
                        
                    # Response with court information
                    response_data = {
                        'success': True,
                        'message': 'Match scheduled successfully',
                        'fixture_type': 'RR_KO',
                        'current_phase': 'round_robin',
                        'match': {
                            'id': match_instance.id,
                            'team1': match_instance.team1.name if match_instance.team1 else 'BYE',
                            'team2': match_instance.team2.name if match_instance.team2 else 'BYE',
                            'round': getattr(match_instance, 'round_number', 1)
                        },
                        'next_available_matches': remaining_matches
                    }
                    
                    if court_instance:
                        response_data['court'] = {
                            'id': court_instance.id,
                            'name': court_instance.name
                        }
                        response_data['position'] = court_position
                        response_data['queue_position'] = queue_position
                        
                        if court_position == "current":
                            response_data['message'] = f"Match scheduled successfully and assigned to {court_instance.name}"
                        else:
                            response_data['message'] = f"Match scheduled and queued for {court_instance.name} (position {queue_position})"
                    
                    return Response(response_data)
                
                except Match.DoesNotExist:
                    return Response(
                        {'error': 'Match not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
            elif current_phase == 'knockout':
                # Handle Knockout phase scheduling
                ko_phase = rr_ko_instance.knockout_phase
                
                if not ko_phase:
                    return Response(
                        {'error': 'Knockout phase not initialized yet'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                bracket_matches = ko_phase.bracket_matches.values_list('id', flat=True)
                
                if match_id not in bracket_matches:
                    return Response(
                        {'error': 'Match not found in knockout bracket matches'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    with transaction.atomic():
                        match_instance = Match.objects.get(id=match_id)
                        
                        # Validate both teams are assigned
                        if not match_instance.team1 or not match_instance.team2:
                            return Response(
                                {'error': 'Match cannot be scheduled - both teams must be assigned'}, 
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Auto-queue logic for court assignment
                        if court_instance:
                            if court_instance.current_match is None:
                                court_instance.current_match = match_instance
                                court_position = "current"
                                queue_position = None
                            else:
                                court_instance.upcoming_matches.add(match_instance)
                                court_position = "queued"
                                queue_position = court_instance.upcoming_matches.count()
                            
                            court_instance.save()
                        
                        # Schedule the match
                        fixture.scheduled_matches.add(match_instance)
                        ko_phase.bracket_matches.remove(match_instance)
                        
                        # Save changes
                        fixture.save()
                        ko_phase.save()
                        
                        # Calculate remaining matches
                        remaining_matches = ko_phase.bracket_matches.filter(
                            team1__isnull=False, 
                            team2__isnull=False
                        ).count()
                        
                    # Response with court information
                    response_data = {
                        'success': True,
                        'message': 'Match scheduled successfully',
                        'fixture_type': 'RR_KO',
                        'current_phase': 'knockout',
                        'match': {
                            'id': match_instance.id,
                            'team1': match_instance.team1.name if match_instance.team1 else 'BYE',
                            'team2': match_instance.team2.name if match_instance.team2 else 'BYE',
                            'stage': match_instance.stage_number,
                            'match_number': match_instance.match_number
                        },
                        'next_available_matches': remaining_matches
                    }
                    
                    if court_instance:
                        response_data['court'] = {
                            'id': court_instance.id,
                            'name': court_instance.name
                        }
                        response_data['position'] = court_position
                        response_data['queue_position'] = queue_position
                        
                        if court_position == "current":
                            response_data['message'] = f"Match scheduled successfully and assigned to {court_instance.name}"
                        else:
                            response_data['message'] = f"Match scheduled and queued for {court_instance.name} (position {queue_position})"
                    
                    return Response(response_data)
                
                except Match.DoesNotExist:
                    return Response(
                        {'error': 'Match not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {'error': f'Unknown phase: {current_phase}'}, 
                    status=status.HTTP_400_BAD_REQUEST
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
    Enhanced with immediate progression, tournament state tracking, and automatic court advancement.
    
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
        - match_completed: Boolean indicating if match finished
        - winner: Winner team name if match completed
        - next_matches_available: Number of new matches ready for scheduling
        - tournament_completed: Boolean indicating if tournament finished
        - court_advancement: Court advancement details (if match was assigned to a court)
            - court_id: ID of the court
            - court_name: Name of the court
            - advanced: Boolean indicating if court advanced
            - previous_match_id: ID of the completed match
            - new_current_match: Details of new current match (if any)
            - court_available: Boolean indicating if court is now available
            - remaining_queue_count: Number of matches still in queue
        
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
        
        # Get match ID and validate
        match_id = request.data.get('match_id')
        
        if not match_id:
            return Response(
                {'error': 'match_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        # Validate action
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
        
        # Enhanced response with tournament state tracking
        if result.get('success', False):
            # Check if match was completed
            match_completed = match_instance.match_state
            
            if match_completed:
                fixture_type = category_instance.fixture.fixtureType
                
                if fixture_type == 'KO':
                    ko_instance = category_instance.fixture.content_object
                    
                    # Count new matches available for scheduling
                    available_matches = ko_instance.bracket_matches.filter(
                        team1__isnull=False, 
                        team2__isnull=False
                    ).count()
                    
                    # Check tournament completion
                    tournament_completed = bool(category_instance.winner)
                    
                    # Build standardized response
                    extra_fields = {}
                    if tournament_completed:
                        extra_fields['tournament_winner'] = category_instance.winner.name
                        extra_fields['message'] = f"Tournament completed! Winner: {category_instance.winner.name}"
                    elif available_matches > 0:
                        extra_fields['message'] = f"Match completed! {available_matches} new matches ready for scheduling"
                    
                    result.update(build_match_completion_response(
                        match_instance, available_matches, tournament_completed, **extra_fields
                    ))
                        
                elif fixture_type == 'RR_KO':
                    rr_ko_instance = category_instance.fixture.content_object
                    current_phase = rr_ko_instance.current_phase
                    
                    if current_phase == 'round_robin':
                        # Update RR phase stats
                        rr_ko_instance.round_robin_phase.update_team_stats(match_instance)
                        
                        # Check if RR phase is complete
                        if rr_ko_instance.check_round_robin_completion():
                            # Automatically create knockout matches
                            rr_phase = rr_ko_instance.round_robin_phase
                            total_teams = rr_phase.rr_teams.count()
                            num_qualified = max(2, min(total_teams // 2, 8))
                            
                            qualified_teams = rr_ko_instance.get_qualified_teams(num_teams=num_qualified)
                            
                            # Prepare match pairings based on seeding
                            matches_data = []
                            has_bye = len(qualified_teams) % 2 != 0
                            bye_team = None
                            
                            if has_bye:
                                # Top seed gets BYE
                                bye_team = qualified_teams[0]
                                remaining_teams = qualified_teams[1:]
                            else:
                                remaining_teams = qualified_teams
                            
                            # Create pairings: highest seed vs lowest seed
                            num_pairs = len(remaining_teams) // 2
                            for i in range(num_pairs):
                                high_seed = remaining_teams[i]
                                low_seed = remaining_teams[-(i + 1)]
                                matches_data.append({
                                    'team_1': high_seed.id,
                                    'team_2': low_seed.id
                                })
                            
                            # Build request data for KoGen
                            ko_request_data = {'matches': matches_data}
                            
                            # Create knockout phase FIRST (before KoGen needs it)
                            try:
                                # Create Knockout instance if not exists
                                if not rr_ko_instance.knockout_phase:
                                    from .models import Knockout
                                    ko_phase = Knockout.objects.create(
                                        category=category_instance
                                    )
                                    rr_ko_instance.knockout_phase = ko_phase
                                    rr_ko_instance.save()
                                
                                # Use context manager to temporarily swap content_object for KoGen
                                with KoGenContentSwap(category_instance.fixture, rr_ko_instance.knockout_phase):
                                    # Initialize KO generator based on sport type
                                    if category_instance.tournament.sport.scoring_type == "sets":
                                        no_sets = category_instance.max_sets
                                        points_win = category_instance.required_points
                                        ko_gen = KoGen(category_instance, ko_request_data, no_sets, points_win)
                                    else:
                                        ko_gen = KoGen(category_instance, ko_request_data)
                                    
                                    # Use KoGen to create bracket structure
                                    ko_result = ko_gen.create_complete_bracket_with_teams()
                                
                                # Check if KoGen returned an error
                                if isinstance(ko_result, dict) and ('error' in ko_result or 'errors' in ko_result):
                                    error_msg = ko_result.get('error', ko_result.get('errors', 'Unknown error'))
                                    raise Exception(f"KoGen failed: {error_msg}")
                                
                                # Mark knockout phase as started
                                rr_ko_instance.knockout_started = True
                                rr_ko_instance.save()
                                
                                ko_instance = rr_ko_instance.knockout_phase
                                total_ko_matches = ko_instance.all_matches.count()
                                available_ko_matches = ko_instance.bracket_matches.filter(
                                    team1__isnull=False,
                                    team2__isnull=False
                                ).count()
                                
                                # Build response
                                result.update({
                                    'match_completed': match_completed,
                                    'winner': match_instance.winner.name if match_instance.winner else None,
                                    'phase_completed': True,
                                    'new_phase': 'knockout',
                                    'qualified_teams': [{'id': t.id, 'name': t.name} for t in qualified_teams],
                                    'knockout_matches_created': total_ko_matches,
                                    'knockout_matches_ready': available_ko_matches,
                                    'has_bye': has_bye,
                                    'message': f'Round Robin completed! Knockout matches auto-created. {available_ko_matches} matches ready to schedule.'
                                })
                                
                                if has_bye and bye_team:
                                    result['bye_team'] = {
                                        'id': bye_team.id,
                                        'name': bye_team.name,
                                        'message': f'{bye_team.name} advances directly (BYE)'
                                    }
                                    
                            except Exception as ko_error:
                                logger.error(f"Error auto-creating KO matches: {str(ko_error)}")
                                result.update({
                                    'match_completed': match_completed,
                                    'winner': match_instance.winner.name if match_instance.winner else None,
                                    'phase_completed': True,
                                    'rr_phase_completed': True,
                                    'qualified_teams': len(qualified_teams),
                                    'error': f'RR completed but failed to create KO matches: {str(ko_error)}',
                                    'message': 'Round Robin phase completed but knockout creation failed. Please contact support.'
                                })
                        else:
                            result.update({
                                'match_completed': match_completed,
                                'winner': match_instance.winner.name if match_instance.winner else None,
                                'message': 'Match completed successfully'
                            })
                            
                    elif current_phase == 'knockout':
                        ko_instance = rr_ko_instance.knockout_phase
                        
                        # Count new matches available for scheduling
                        available_matches = ko_instance.bracket_matches.filter(
                            team1__isnull=False, 
                            team2__isnull=False
                        ).count()
                        
                        # Check tournament completion
                        tournament_completed = bool(category_instance.winner)
                        
                        # Build standardized response
                        extra_fields = {}
                        if tournament_completed:
                            extra_fields['tournament_winner'] = category_instance.winner.name
                            extra_fields['message'] = f"Tournament completed! Winner: {category_instance.winner.name}"
                        elif available_matches > 0:
                            extra_fields['message'] = f"Match completed! {available_matches} new matches ready for scheduling"
                        
                        result.update(build_match_completion_response(
                            match_instance, available_matches, tournament_completed, **extra_fields
                        ))
                
                elif fixture_type == 'RR':
                    # For Round Robin, just indicate match completion
                    result.update({
                        'match_completed': match_completed,
                        'winner': match_instance.winner.name if match_instance.winner else None,
                        'message': 'Match completed successfully'
                    })
        
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

@api_view(['GET'])
@organizer_required_api
def tournament_details(request, tournament_id):
    """
    Get detailed information about a tournament including all its categories, teams, and scheduled matches.
    
    This endpoint returns comprehensive tournament information including:
    - Tournament basic details (name, dates, venue, etc.)
    - All categories within the tournament with detailed team information
    - Complete list of all teams across all categories
    - Scheduled matches for each category with detailed match information
    - Tournament-wide scheduled matches summary
    - Registration status and team counts for each category
    - Match completion statistics and tournament progress
    
    HTTP Method: GET
    
    URL Parameters:
        - tournament_id: ID of the tournament to retrieve details for
    
    Returns:
        Response: JSON containing:
        - tournament: Complete tournament information
        - categories: List of all categories with enhanced team details and scheduled matches
        - teams: List of all teams across all categories
        - scheduled_matches: List of all scheduled matches across all categories
        - total_teams: Total number of teams in the tournament
        - total_categories: Total number of categories in the tournament
        - total_scheduled_matches: Total number of scheduled matches in the tournament
        - total_completed_matches: Total number of completed matches
        - total_pending_matches: Total number of pending matches
        - tournament_statistics: Overall tournament progress and completion statistics
        
        Each category includes:
        - scheduled_matches: Array of match details with teams, scores, and status
        - scheduled_matches_count: Number of scheduled matches in the category
        - completed_matches_count: Number of completed matches in the category
        - pending_matches_count: Number of pending matches in the category
        
        Each match includes:
        - Basic match info (id, teams, winner, status)
        - Sport-specific scoring (sets won for set-based sports, simple scores)
        - Current set scores (detailed point-by-point scores for each set in set-based sports)
        - Match metadata (stage, match number, fixture type)
        
        Or error details with appropriate status code.
    """
    try:
        # Get tournament and verify it belongs to the user's organization
        tournament = Tournament.objects.get(id=tournament_id)
        
        # Check if the user is admin of the tournament's organization
        if tournament.organization.admin != request.user:
            return Response(
                {'error': 'You do not have permission to view this tournament'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize tournament data with sport details
        tournament_serializer = TournamentDetailSerializer(tournament)
        
        # Get all categories for this tournament with related data
        categories = Category.objects.filter(tournament=tournament).prefetch_related('teams')
        
        # Prepare category data with enhanced team information
        category_data = []
        all_teams = []  # Collect all teams across categories
        all_scheduled_matches = []  # Collect all scheduled matches across categories
        
        for category in categories:
            # Get teams for this category with additional details
            category_teams = []
            for team in category.teams.all():
                team_info = {
                    'id': team.id,
                    'name': team.name,
                    'category_id': category.id,
                    'category_name': category.name
                }
                category_teams.append(team_info)
                all_teams.append(team_info)  # Add to overall teams list
            
            # Get scheduled matches for this category
            category_scheduled_matches = []
            if hasattr(category, 'fixture') and category.fixture:
                scheduled_matches = category.fixture.scheduled_matches.select_related(
                    'team1', 'team2', 'winner', 'sport'
                ).prefetch_related('sets').all()
                
                for match in scheduled_matches:
                    match_info = {
                        'id': match.id,
                        'team1': {
                            'id': match.team1.id,
                            'name': match.team1.name
                        } if match.team1 else None,
                        'team2': {
                            'id': match.team2.id,
                            'name': match.team2.name
                        } if match.team2 else None,
                        'winner': {
                            'id': match.winner.id,
                            'name': match.winner.name
                        } if match.winner else None,
                        'match_state': match.match_state,
                        'match_number': match.match_number,
                        'stage_number': match.stage_number,
                        'sport': match.sport.name,
                        'category_id': category.id,
                        'category_name': category.name,
                        'fixture_type': category.fixture.fixtureType,
                        # Add scoring information based on sport type
                        'team1_sets_won': match.team1_sets_won if match.sport.scoring_type == 'sets' else None,
                        'team2_sets_won': match.team2_sets_won if match.sport.scoring_type == 'sets' else None,
                        'team1_simple_score': match.score_system.team1_score if match.sport.scoring_type == 'simple' and match.score_system else None,
                        'team2_simple_score': match.score_system.team2_score if match.sport.scoring_type == 'simple' and match.score_system else None
                    }
                    
                    # Add current set scores for set-based sports
                    if match.sport.scoring_type == 'sets':
                        set_scores = []
                        for set_score in match.sets.all().order_by('set_number'):
                            set_info = {
                                'set_number': set_score.set_number,
                                'team1_points': set_score.team1_points,
                                'team2_points': set_score.team2_points,
                                'set_winner': {
                                    'id': set_score.winner.id,
                                    'name': set_score.winner.name
                                } if set_score.winner else None,
                                'set_completed': set_score.set_state
                            }
                            set_scores.append(set_info)
                        match_info['current_set_scores'] = set_scores
                    else:
                        match_info['current_set_scores'] = None
                    category_scheduled_matches.append(match_info)
                    all_scheduled_matches.append(match_info)  # Add to overall matches list
            
            category_info = {
                'id': category.id,
                'name': category.name,
                'details': category.details,
                'price': str(category.price),
                'registration_status': category.registration_status,
                'reg_status': category.reg_status,
                'teams_count': category.teams.count(),
                'teams': category_teams,
                'winner': {
                    'id': category.winner.id,
                    'name': category.winner.name
                } if category.winner else None,
                'has_fixture': hasattr(category, 'fixture') and category.fixture is not None,
                'fixture_type': category.fixture.fixtureType if hasattr(category, 'fixture') and category.fixture else None,
                'scheduled_matches': category_scheduled_matches,
                'scheduled_matches_count': len(category_scheduled_matches),
                'completed_matches_count': len([m for m in category_scheduled_matches if m['match_state']]),
                'pending_matches_count': len([m for m in category_scheduled_matches if not m['match_state']])
            }
            
            # Add set-based sport specific information
            if tournament.sport.scoring_type == 'sets':
                category_info.update({
                    'max_sets': category.max_sets,
                    'required_points': category.required_points
                })
            
            category_data.append(category_info)
        
        return Response({
            'tournament': tournament_serializer.data,
            'categories': category_data,
            'teams': all_teams,
            'total_teams': len(all_teams),
            'total_categories': len(category_data),
            'scheduled_matches': all_scheduled_matches,
            'total_scheduled_matches': len(all_scheduled_matches),
            'total_completed_matches': len([m for m in all_scheduled_matches if m['match_state']]),
            'total_pending_matches': len([m for m in all_scheduled_matches if not m['match_state']]),
        })
    
    except Tournament.DoesNotExist:
        return Response(
            {'error': 'Tournament not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        logger.error(f"Error fetching tournament details: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@organizer_required_api
def get_fixture_details(request, tournament_id, category_id):
    """
    Get fixture details for KO diagram or RR table visualization.
    
    This endpoint returns structured data for building tournament visualizations
    based on actual Match records with stage_number and match_number,
    including live scoring data from SetScore/SimpleScore models.
    
    HTTP Method: GET
    
    URL Parameters:
        - tournament_id: ID of the tournament
        - category_id: ID of the category containing the fixture
    
    Returns:
        For KO fixtures:
        {
            "fixture_type": "KO",
            "sport_type": "simple" | "sets",
            "stages": [
                {
                    "stageIndex": 4,
                    "name": "First Round",
                    "matches": [
                        {
                            "id": "s4m1",
                            "team1": "Team A",
                            "team2": "Team B", 
                            "winner": "Team A",
                            "team1Score": 21,
                            "team2Score": 18
                        }
                    ]
                }
            ]
        }
        
        For RR fixtures:
        {
            "fixture_type": "RR",
            "sport_type": "simple" | "sets", 
            "teams": ["Team A", "Team B", ...],
            "results": [
                {
                    "team1": "Team A",
                    "team2": "Team B",
                    "score1": 21,
                    "score2": 18
                }
            ]
        }
        
        Or error details with appropriate status code.
    """
    try:
        # Validate and get category
        category = Category.objects.get(id=category_id, tournament_id=tournament_id)
        
        # Check if the user is admin of the tournament's organization
        if category.tournament.organization.admin != request.user:
            return Response(
                {'error': 'You do not have permission to view this fixture'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not hasattr(category, 'fixture') or not category.fixture:
            return Response(
                {'error': 'Fixture not created yet'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fixture = category.fixture
        
        if fixture.fixtureType == 'KO':
            return Response(build_ko_fixture_data(category, fixture))
        elif fixture.fixtureType == 'RR':
            return Response(build_rr_fixture_data(category, fixture))
        elif fixture.fixtureType == 'RR_KO':
            return Response(build_rr_ko_fixture_data(category, fixture))
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
    except Exception as e:
        logger.error(f"Error fetching fixture details: {str(e)}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def build_ko_fixture_data(category, fixture):
    """
    Build KO fixture data from Match records organized by stage_number and match_number.
    
    Args:
        category: Category instance
        fixture: Fixture instance
        
    Returns:
        dict: Structured KO fixture data for frontend visualization
    """
    ko_instance = fixture.content_object
    sport = category.tournament.sport
    
    # Get all matches with proper relationships
    all_matches = ko_instance.all_matches.select_related(
        'team1', 'team2', 'winner'
    ).prefetch_related('sets').all()
    
    if not all_matches.exists():
        return {
            "fixture_type": "KO",
            "sport_type": sport.scoring_type,
            "stages": [],
            "message": "No matches created yet"
        }
    
    # Group matches by stage_number
    stages_dict = {}
    for match in all_matches:
        stage_num = match.stage_number
        if stage_num not in stages_dict:
            stages_dict[stage_num] = []
        stages_dict[stage_num].append(match)
    
    # Build stages array (highest stage number first - early rounds)
    stages = []
    stage_numbers = sorted(stages_dict.keys(), reverse=True)
    
    for i, stage_num in enumerate(stage_numbers):
        stage_matches = sorted(stages_dict[stage_num], key=lambda x: x.match_number or 0)
        
        # Generate proper stage name
        stage_name = generate_ko_stage_name(i, len(stage_numbers), len(stage_matches))
        
        matches_data = []
        for match in stage_matches:
            # Determine if this is a first round (highest stage number) or later round
            is_first_round = stage_num == max(stage_numbers)
            
            match_data = {
                "id": f"s{stage_num}m{match.match_number or 0}",
                "team1": match.team1.name if match.team1 else ("BYE" if is_first_round else "TBD"),
                "team2": match.team2.name if match.team2 else ("BYE" if is_first_round else "TBD"),
                "winner": match.winner.name if match.winner else None,
                "match_completed": match.match_state
            }
            
            # Add scoring based on sport type
            if sport.scoring_type == 'simple':
                scores = get_simple_scores(match)
                match_data.update(scores)
            else:  # sets
                scores = get_set_scores(match)
                match_data.update(scores)
                
            matches_data.append(match_data)
        
        stages.append({
            "stageIndex": stage_num,
            "name": stage_name,
            "matches": matches_data
        })
    
    return {
        "fixture_type": "KO",
        "sport_type": sport.scoring_type,
        "stages": stages
    }


def build_rr_fixture_data(category, fixture):
    """
    Build RR fixture data from all matches and team statistics.
    
    Args:
        category: Category instance
        fixture: Fixture instance
        
    Returns:
        dict: Structured RR fixture data for frontend visualization
    """
    rr_instance = fixture.content_object
    sport = category.tournament.sport
    
    # Get all teams
    teams = [team.name for team in category.teams.all()]
    
    # Get all matches (both scheduled and completed)
    all_matches = rr_instance.all_matches.select_related(
        'team1', 'team2', 'winner'
    ).prefetch_related('sets').all()
    
    results = []
    for match in all_matches:
        if match.team1 and match.team2:  # Skip BYE matches if any
            result_data = {
                "team1": match.team1.name,
                "team2": match.team2.name,
                "match_completed": match.match_state
            }
            
            # Add scoring based on sport type and match completion
            if match.match_state:  # Completed match
                if sport.scoring_type == 'simple':
                    scores = get_simple_scores(match)
                    result_data.update({
                        "score1": scores["team1Score"],
                        "score2": scores["team2Score"]
                    })
                else:  # sets
                    result_data.update({
                        "score1": match.team1_sets_won,
                        "score2": match.team2_sets_won
                    })
            else:  # Pending match
                result_data.update({
                    "score1": None,
                    "score2": None
                })
                
            results.append(result_data)
    
    return {
        "fixture_type": "RR",
        "sport_type": sport.scoring_type,
        "teams": teams,
        "results": results
    }


def build_rr_ko_fixture_data(category, fixture):
    """
    Build RR_KO fixture data based on current phase.
    
    Args:
        category: Category instance
        fixture: Fixture instance
        
    Returns:
        dict: Structured RR_KO fixture data for frontend visualization
    """
    rr_ko_instance = fixture.content_object
    sport = category.tournament.sport
    current_phase = rr_ko_instance.current_phase
    
    # Base response with fixture type and current phase info
    response_data = {
        "fixture_type": "RR_KO",
        "sport_type": sport.scoring_type,
        "current_phase": current_phase,
        "round_robin_completed": rr_ko_instance.round_robin_completed,
        "knockout_started": rr_ko_instance.knockout_started
    }
    
    # Round Robin phase data (always include if RR phase exists)
    if rr_ko_instance.round_robin_phase:
        rr_teams = [team.name for team in category.teams.all()]
        rr_matches = rr_ko_instance.round_robin_phase.all_matches.select_related(
            'team1', 'team2', 'winner'
        ).prefetch_related('sets').all()
        
        rr_results = []
        for match in rr_matches:
            if match.team1 and match.team2:
                result_data = {
                    "team1": match.team1.name,
                    "team2": match.team2.name,
                    "match_completed": match.match_state
                }
                
                if match.match_state:
                    if sport.scoring_type == 'simple':
                        scores = get_simple_scores(match)
                        result_data.update({
                            "score1": scores["team1Score"],
                            "score2": scores["team2Score"]
                        })
                    else:
                        result_data.update({
                            "score1": match.team1_sets_won,
                            "score2": match.team2_sets_won
                        })
                else:
                    result_data.update({
                        "score1": None,
                        "score2": None
                    })
                    
                rr_results.append(result_data)
        
        response_data["round_robin"] = {
            "teams": rr_teams,
            "results": rr_results
        }
    
    # Knockout phase data (only if KO has started)
    if rr_ko_instance.knockout_started and rr_ko_instance.knockout_phase:
        ko_matches = rr_ko_instance.knockout_phase.all_matches.select_related(
            'team1', 'team2', 'winner'
        ).prefetch_related('sets').all()
        
        if ko_matches.exists():
            stages_dict = {}
            for match in ko_matches:
                stage_num = match.stage_number
                if stage_num not in stages_dict:
                    stages_dict[stage_num] = []
                stages_dict[stage_num].append(match)
            
            stages = []
            stage_numbers = sorted(stages_dict.keys(), reverse=True)
            
            for i, stage_num in enumerate(stage_numbers):
                stage_matches = sorted(stages_dict[stage_num], key=lambda x: x.match_number or 0)
                stage_name = generate_ko_stage_name(i, len(stage_numbers), len(stage_matches))
                
                matches_data = []
                for match in stage_matches:
                    is_first_round = stage_num == max(stage_numbers)
                    
                    match_data = {
                        "id": f"s{stage_num}m{match.match_number or 0}",
                        "team1": match.team1.name if match.team1 else ("BYE" if is_first_round else "TBD"),
                        "team2": match.team2.name if match.team2 else ("BYE" if is_first_round else "TBD"),
                        "winner": match.winner.name if match.winner else None,
                        "match_completed": match.match_state
                    }
                    
                    if sport.scoring_type == 'simple':
                        scores = get_simple_scores(match)
                        match_data.update(scores)
                    else:
                        scores = get_set_scores(match)
                        match_data.update(scores)
                        
                    matches_data.append(match_data)
                
                stages.append({
                    "stageIndex": stage_num,
                    "name": stage_name,
                    "matches": matches_data
                })
            
            response_data["knockout"] = {
                "stages": stages
            }
    
    return response_data


def generate_ko_stage_name(stage_index, total_stages, match_count):
    """
    Generate appropriate stage name for knockout tournaments.
    
    Args:
        stage_index: Index in the stages array (0 is first/earliest round)
        total_stages: Total number of stages in tournament
        match_count: Number of matches in this stage
        
    Returns:
        str: Human-readable stage name
    """
    # Last stage (finals)
    if stage_index == total_stages - 1:
        return "Finals"
    # Second to last stage (semi-finals)
    elif stage_index == total_stages - 2 and match_count == 2:
        return "Semi Finals"
    # Third to last stage (quarter-finals)
    elif stage_index == total_stages - 3 and match_count == 4:
        return "Quarter Finals"
    # Early rounds
    else:
        # Use ordinal numbering for early rounds
        round_number = stage_index + 1
        if round_number == 1:
            return "First Round"
        elif round_number == 2:
            return "Second Round"
        elif round_number == 3:
            return "Third Round"
        else:
            return f"Round {round_number}"


def get_simple_scores(match):
    """
    Get simple scoring data for a match.
    
    Args:
        match: Match instance
        
    Returns:
        dict: Team scores or null if no score system exists
    """
    # If match hasn't started or teams aren't determined, return zero scores
    if not match.team1 or not match.team2:
        return {
            "team1Score": 0,
            "team2Score": 0
        }
    
    try:
        if hasattr(match, 'score_system') and match.score_system:
            return {
                "team1Score": match.score_system.team1_score,
                "team2Score": match.score_system.team2_score
            }
    except:
        pass
    
    return {
        "team1Score": 0,
        "team2Score": 0
    }


def get_set_scores(match):
    """
    Get set-based scoring data for a match.
    
    Args:
        match: Match instance
        
    Returns:
        dict: Sets won by each team plus current set scores
    """
    # If teams aren't determined (TBD), return zero scores
    if not match.team1 or not match.team2:
        return {
            "team1Score": 0,  # Sets won
            "team2Score": 0,  # Sets won  
            "currentSetScore": {
                "team1Points": 0,
                "team2Points": 0
            }
        }
    
    # Get total sets won by each team
    team1_sets = match.team1_sets_won
    team2_sets = match.team2_sets_won
    
    # Get current set in progress scores
    current_set = match.current_set
    current_set_scores = {
        "team1Points": current_set.team1_points if current_set else 0,
        "team2Points": current_set.team2_points if current_set else 0
    }
    
    return {
        "team1Score": team1_sets,  # Sets won
        "team2Score": team2_sets,  # Sets won  
        "currentSetScore": current_set_scores  # Points in current set
    }


@api_view(['GET'])
@organizer_required_api
def list_courts(request, tournament_id):
    """
    List all courts for a tournament owned by the requesting organizer.

    Returns: { "courts": [ CourtSerializer... ] }
    """
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        if tournament.organization.admin != request.user:
            return Response({'error': 'You do not have permission to view courts for this tournament'}, status=status.HTTP_403_FORBIDDEN)

        courts = Court.objects.filter(tournament=tournament).select_related('current_match__team1', 'current_match__team2', 'current_match__category')
        data = CourtSerializer(courts, many=True).data
        return Response({"courts": data})
    except Tournament.DoesNotExist:
        return Response({'error': 'Tournament not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error listing courts: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@organizer_required_api
def create_court(request, tournament_id):
    """
    Create a new court for the given tournament. Prevent duplicate names per tournament.
    Body: { "name": "Court 1" }
    """
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        if tournament.organization.admin != request.user:
            return Response({'error': 'You do not have permission to create courts for this tournament'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CourtCreateUpdateSerializer(data=request.data, context={'tournament_id': tournament.id})
        if serializer.is_valid():
            court = serializer.save()
            return Response(CourtSerializer(court).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Tournament.DoesNotExist:
        return Response({'error': 'Tournament not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating court: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@organizer_required_api
def court_detail(request, court_id):
    """
    Retrieve, update, or delete a court. Delete blocked if current or queued matches exist.
    """
    try:
        court = Court.objects.select_related('tournament__organization__admin', 'current_match__team1', 'current_match__team2', 'current_match__category').get(id=court_id)
    except Court.DoesNotExist:
        return Response({'error': 'Court not found'}, status=status.HTTP_404_NOT_FOUND)

    # Permission check
    if court.tournament.organization.admin != request.user:
        return Response({'error': 'You do not have permission to access this court'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Include detailed upcoming matches for the detail view
        serializer = CourtSerializer(court, context={'include_upcoming_details': True})
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = CourtCreateUpdateSerializer(instance=court, data=request.data, context={'tournament_id': court.tournament.id})
        if serializer.is_valid():
            court = serializer.save()
            return Response(CourtSerializer(court).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    if court.current_match is not None or court.upcoming_matches.exists():
        return Response({'error': 'Court cannot be deleted while matches are assigned'}, status=status.HTTP_400_BAD_REQUEST)
    court.delete()
    return Response({'success': True, 'message': 'Court deleted'})



