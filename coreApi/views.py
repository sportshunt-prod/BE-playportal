from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from sportshunt.utils import login_required_api, get_user_from_token
from sportshunt.utils.authentication import get_auth_response
from sportshunt.utils.google_auth import verify_google_token, get_or_create_google_user
from sportshunt.utils.razorpay_utils import razorpay_manager
from rest_framework import status
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from .models import *
from organizationApi.models import Tournament, Category, Sport, Team
from organizationApi.serializers import SportDetailSerializer
from .serializers import (
    TournamentListSerializer, UserProfileSerializer, TournamentDetailSerializer,
    CategorySerializer, RegisterSerializer, LoginSerializer, GoogleAuthSerializer,
    CreateOrderSerializer, VerifyPaymentSerializer
)
import jwt
from datetime import datetime, timedelta
import uuid
import json
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
    Get a list of upcoming, ongoing, and past tournaments.
    
    This endpoint provides lists of upcoming tournaments (start date in the future),
    ongoing tournaments (current date between start and end date), and past tournaments
    (end date in the past), limited to 4 of each.
    
    HTTP Method: GET
    
    Returns:
        Response: JSON containing:
        - upcoming_tournaments: List of tournaments with future start dates (max 4)
        - ongoing_tournaments: List of tournaments currently in progress (max 4)
        - past_tournaments: List of tournaments with past end dates (max 4)
    """
    current_date = timezone.now().date()
    # Get upcoming tournaments
    upcoming_tournaments = Tournament.objects.filter(
        start_date__gt=current_date
    ).select_related('organization', 'sport').order_by('start_date')[:4]
    
    # Get ongoing tournaments
    ongoing_tournaments = Tournament.objects.filter(
        start_date__lte=current_date,
        end_date__gte=current_date
    ).select_related('organization', 'sport').order_by('start_date')[:4]
    
    # Get past tournaments
    past_tournaments = Tournament.objects.filter(
        end_date__lt=current_date
    ).select_related('organization', 'sport').order_by('-end_date')[:4]
    
    # Serialize the data
    upcoming_serializer = TournamentListSerializer(upcoming_tournaments, many=True)
    ongoing_serializer = TournamentListSerializer(ongoing_tournaments, many=True)
    past_serializer = TournamentListSerializer(past_tournaments, many=True)
    
    return Response({
        'upcoming_tournaments': upcoming_serializer.data,
        'ongoing_tournaments': ongoing_serializer.data,
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

@api_view(['GET'])
def sports_list_api(request):
    """
    Get a list of all available sports.

    This endpoint provides a list of all sports available in the system.
    No authentication required - public endpoint.

    HTTP Method: GET

    Returns:
        Response: JSON array containing all sports with their id, name, and scoring_type
        Example: [{"id": 1, "name": "Tennis", "scoring_type": "sets"}, ...]
    """
    sports = Sport.objects.all().order_by('name')
    serializer = SportDetailSerializer(sports, many=True)
    return Response(serializer.data)


# Razorpay Payment Integration Views

@api_view(['POST'])
@login_required_api
@transaction.atomic
def create_order(request):
    """
    Create a Razorpay order for team registration payment.
    
    HTTP Method: POST
    Auth: Required (Bearer token)
    
    Request Body:
        - tournament_id: ID of tournament
        - category_id: ID of category
        - team_name: Name of team
        - amount: Amount in rupees (will be converted to paise for Razorpay)
    
    Returns:
        Response: Order details with razorpay_order_id for frontend checkout
    """
    user = request.user  # Get user from request object set by decorator
    
    serializer = CreateOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Use select_related to reduce DB queries
        tournament = Tournament.objects.select_related('organization', 'sport').get(
            id=serializer.validated_data['tournament_id']
        )
        category = Category.objects.select_related('sport', 'fixture').get(
            id=serializer.validated_data['category_id']
        )
        
        # Check if category registration is open
        if not category.registration_status:
            return Response(
                {'error': 'Registration closed for this category'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique order ID
        order_id = f"order_{datetime.now().timestamp()}_{uuid.uuid4().hex[:6]}"
        
        # Create Order record in DB (with pending status)
        amount_rupees = serializer.validated_data['amount']
        amount_paise = amount_rupees * 100  # Razorpay expects paise
        
        order = Order.objects.create(
            order_id=order_id,
            user=user,
            amount=amount_rupees,  # Store in rupees for readability
            team_name=serializer.validated_data['team_name'],
            tournament_instance=tournament,
            category_instance=category,
            payment_status='pending'
        )
        
        # Create Razorpay order
        razorpay_order = razorpay_manager.create_order(
            amount=amount_paise,
            order_id=order_id,
            notes={
                'tournament': tournament.name,
                'category': category.name,
                'team_name': serializer.validated_data['team_name'],
                'user_email': user.email
            }
        )
        
        # Store Razorpay order ID
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        logger.info(
            "Order created successfully",
            extra={'order_id': order_id, 'user_id': user.id, 'amount': amount_rupees}
        )
        
        return Response({
            'order_id': order_id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': amount_rupees,
            'currency': 'INR',
            'tournament': {'id': tournament.id, 'name': tournament.name},
            'category': {'id': category.id, 'name': category.name},
            'team_name': serializer.validated_data['team_name'],
            'created_at': order.order_timestamp.isoformat()
        }, status=status.HTTP_201_CREATED)
    
    except Tournament.DoesNotExist:
        logger.warning(
            "Tournament not found",
            extra={'tournament_id': serializer.validated_data.get('tournament_id'), 'user_id': user.id}
        )
        return Response(
            {'error': 'tournament_not_found', 'message': 'Tournament not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Category.DoesNotExist:
        logger.warning(
            "Category not found",
            extra={'category_id': serializer.validated_data.get('category_id'), 'user_id': user.id}
        )
        return Response(
            {'error': 'category_not_found', 'message': 'Category not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(
            "Order creation failed",
            extra={
                'order_id': order_id if 'order_id' in locals() else None,
                'user_id': user.id,
                'tournament_id': serializer.validated_data.get('tournament_id'),
                'category_id': serializer.validated_data.get('category_id'),
                'error_type': type(e).__name__,
                'error_message': str(e)
            },
            exc_info=True
        )
        return Response(
            {'error': 'payment_order_creation_failed', 'message': 'Unable to initiate payment. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@login_required_api
@transaction.atomic
def verify_payment(request):
    """
    Verify Razorpay payment signature and create team registration.
    
    HTTP Method: POST
    Auth: Required (Bearer token)
    
    Request Body:
        - order_id: Order ID from create_order response
        - razorpay_payment_id: Payment ID from Razorpay
        - razorpay_signature: Signature from Razorpay
    
    Returns:
        Response: Verification status and team details
    """
    user = request.user  # Get user from request object set by decorator
    
    serializer = VerifyPaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Fetch order from DB with related data (optimize queries)
        order = Order.objects.select_related(
            'user', 'tournament_instance', 'category_instance', 'team_instance'
        ).get(order_id=serializer.validated_data['order_id'])
        
        # IDEMPOTENCY GUARD 1: If already completed, return success (handle retries safely)
        if order.payment_status == 'completed':
            logger.info(
                "Payment already verified (idempotent retry)",
                extra={'order_id': order.order_id, 'user_id': user.id}
            )
            return Response({
                'status': 'payment_verified',
                'message': 'Payment already verified (duplicate request)',
                'team_id': order.team_instance.id if order.team_instance else None,
                'team_name': order.team_name,
                'is_duplicate': True
            })
        
        # Verify payment signature
        is_valid = razorpay_manager.verify_payment_signature(
            order.razorpay_order_id,
            serializer.validated_data['razorpay_payment_id'],
            serializer.validated_data['razorpay_signature']
        )
        
        if not is_valid:
            order.payment_status = 'failed'
            order.save()
            logger.warning(
                "Invalid payment signature",
                extra={'order_id': order.order_id, 'user_id': user.id}
            )
            return Response(
                {'error': 'invalid_signature', 'message': 'Payment verification failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update Order with payment details
        order.payment_id = serializer.validated_data['razorpay_payment_id']
        order.signature = serializer.validated_data['razorpay_signature']
        order.payment_status = 'completed'
        order.payment_timestamp = timezone.now()
        order.save()
        
        # IDEMPOTENCY GUARD 2: Check if team already created (webhook may have created it)
        if order.team_instance:
            # Team already exists (created by webhook or previous verification)
            team = order.team_instance
            logger.info(
                "Team already exists for order",
                extra={
                    'order_id': order.order_id,
                    'team_id': team.id,
                    'user_id': user.id
                }
            )
        else:
            # Create Team record only if not already created
            team = Team.objects.create(
                name=order.team_name,
                category=order.category_instance,
            )
            order.team_instance = team
            order.save()
            
            logger.info(
                "Payment verified and team created",
                extra={
                    'order_id': order.order_id,
                    'team_id': team.id,
                    'user_id': user.id,
                    'tournament_id': order.tournament_instance.id,
                    'category_id': order.category_instance.id
                }
            )
        
        # Both paths guarantee team is defined; safe to reference in response
        return Response({
            'status': 'payment_verified',
            'message': 'Team registered successfully',
            'team_id': team.id,
            'team_name': team.name,
            'category': order.category_instance.name,
            'tournament': order.tournament_instance.name,
            'payment_id': order.payment_id,
            'amount': f"{order.amount} INR"
        })
    
    except Order.DoesNotExist:
        logger.warning(
            "Order not found for verification",
            extra={'order_id': serializer.validated_data.get('order_id'), 'user_id': user.id}
        )
        return Response(
            {'error': 'order_not_found', 'message': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(
            "Payment verification failed",
            extra={
                'order_id': serializer.validated_data.get('order_id'),
                'user_id': user.id,
                'payment_id': serializer.validated_data.get('razorpay_payment_id'),
                'error_type': type(e).__name__,
                'error_message': str(e)
            },
            exc_info=True
        )
        return Response(
            {'error': 'payment_verification_failed', 'message': 'Payment verification failed. Please contact support if this persists.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
@transaction.atomic
def razorpay_webhook(request):
    """
    Handle Razorpay webhook events (payment.authorized, payment.failed, etc).
    
    Verifies webhook signature and updates order status.
    Authoritative source of truth for payment state (handles offline/retries).
    
    HTTP Method: POST
    Header: X-Razorpay-Signature (for verification)
    
    Body: Razorpay event JSON with payment/order details
    
    Returns:
        Response: Status acknowledgement
    """
    
    try:
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_body = request.body
        
        # Verify webhook signature
        if not razorpay_manager.verify_webhook_signature(webhook_body, webhook_signature):
            logger.warning("Invalid webhook signature")
            return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Parse event
        event = json.loads(webhook_body)
        event_type = event.get('event')
        payload = event.get('payload', {})
        
        logger.info(
            "Webhook received",
            extra={'event_type': event_type}
        )
        
        # Route by event type
        if event_type == 'payment.authorized':
            payment = payload.get('payment', {}).get('entity', {})
            order_data = payload.get('order', {}).get('entity', {})
            
            razorpay_order_id = order_data.get('id')
            razorpay_payment_id = payment.get('id')
            
            order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
            if order:
                order.payment_id = razorpay_payment_id
                order.payment_status = 'completed'
                order.payment_timestamp = timezone.now()
                order.save()
                
                if not order.team_instance:
                    team = Team.objects.create(
                        name=order.team_name,
                        category=order.category_instance,
                    )
                    order.team_instance = team
                    order.save()
                    logger.info(
                        "Team created via webhook (authorized)",
                        extra={'order_id': order.order_id, 'team_id': team.id}
                    )
        
        elif event_type == 'payment.captured':
            payment = payload.get('payment', {}).get('entity', {})
            order_data = payload.get('order', {}).get('entity', {})
            
            razorpay_order_id = order_data.get('id')
            razorpay_payment_id = payment.get('id')
            
            order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
            if order and order.payment_status != 'completed':
                order.payment_id = razorpay_payment_id
                order.payment_status = 'completed'
                order.payment_timestamp = timezone.now()
                order.save()
                
                if not order.team_instance:
                    team = Team.objects.create(
                        name=order.team_name,
                        category=order.category_instance,
                    )
                    order.team_instance = team
                    order.save()
                    logger.info(
                        "Team created via webhook (captured)",
                        extra={'order_id': order.order_id, 'team_id': team.id}
                    )
        
        elif event_type == 'payment.failed':
            payment = payload.get('payment', {}).get('entity', {})
            order_data = payload.get('order', {}).get('entity', {})
            
            razorpay_order_id = order_data.get('id')
            
            order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
            if order:
                order.payment_status = 'failed'
                order.save()
                logger.warning(
                    "Payment failed via webhook",
                    extra={'order_id': order.order_id}
                )
        
        return Response({'status': 'received'}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(
            "Webhook processing failed",
            extra={'error_type': type(e).__name__, 'error_message': str(e)},
            exc_info=True
        )
        return Response({'status': 'received'}, status=status.HTTP_200_OK)