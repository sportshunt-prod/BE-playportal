# Razorpay Payment Integration Guide

## Overview

This document outlines the complete Razorpay payment integration flow for team registration and tournament participation fees.

**Current State**: The `Order` model exists in `coreApi/models.py` with fields for payment tracking but Razorpay API integration is not yet implemented.

**Integration Point**: Team registration → Payment → Order verification → Team confirmation

---

## Payment Flow Architecture

```
┌─────────────┐
│   Frontend  │
│   (React)   │
└──────┬──────┘
       │
       ├─ 1. User selects team + tournament category
       │      Request: POST /team-registration/
       │      Response: order_id, amount, tournament/team details
       │
       ▼
   ┌───────────────────┐
   │  Django Backend   │
   │  POST /order/     │
   └───────┬───────────┘
           │
           ├─ 2. Create Order (DB)
           │      - order_id (PK)
           │      - amount, user, team_name
           │      - tournament/category refs
           │      - payment_id: null, signature: null
           │
           ▼
      ┌─────────────────┐
      │   Razorpay API  │
      │   Create Order  │
      └────────┬────────┘
               │
               ├─ 3. Response: razorpay_order_id
               │      (Store in Order.razorpay_order_id)
               │
               ▼
   ┌─────────────────────────┐
   │  Frontend - Razorpay    │
   │  Checkout Widget        │
   └────────┬────────────────┘
            │
            ├─ 4. User enters card details
            │      Payment processed by Razorpay
            │
            ▼
      ┌────────────────────────┐
      │  Razorpay - Payment    │
      │  Success/Failure       │
      └────────┬───────────────┘
               │
               ├─ 5a. Success:
               │       - payment_id
               │       - signature
               │       Send to frontend
               │
               ├─ 5b. Failure:
               │       - error message
               │       - retry or cancel
               │
               ▼
   ┌──────────────────────────────┐
   │  Frontend - Verification     │
   │  POST /verify-payment/       │
   └────────┬─────────────────────┘
            │
            ├─ 6. Send:
            │      - order_id
            │      - razorpay_payment_id
            │      - razorpay_signature
            │
            ▼
   ┌──────────────────────────────────┐
   │  Django Backend                  │
   │  Verify Signature & Create Team  │
   └────────┬─────────────────────────┘
            │
            ├─ 7. Verify signature with Razorpay secret
            │      If invalid: return error
            │      If valid: proceed
            │
            ├─ 8. Update Order:
            │      - payment_id = razorpay_payment_id
            │      - signature = razorpay_signature
            │      - status = completed
            │
            ├─ 9. Create Team record:
            │      - Link to User, Category, Tournament
            │      - Set paid status
            │
            ▼
   ┌──────────────────────────┐
   │  Frontend - Confirmation │
   │  Team Registered         │
   │  Receipt/Confirmation    │
   └──────────────────────────┘
```

---

## Backend Implementation Checklist

### 1. Environment Configuration (`.env`)
```
# Razorpay API Credentials
RAZORPAY_KEY_ID=your_key_id_here
RAZORPAY_KEY_SECRET=your_key_secret_here
```

### 2. Settings Configuration (`sportshunt/conf/dev.py` and `prod.py`)
```python
import os

# Razorpay Configuration
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# Validate in dev/prod
if DEBUG:  # Development
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise ValueError("Missing Razorpay credentials in environment variables")
```

### 3. Install Razorpay Package
```bash
pip install razorpay
# Add to requirements.txt: razorpay>=1.4.1
```

### 4. Utility Function: Razorpay Client (`sportshunt/utils/razorpay_utils.py`)

**Location**: Create new file `sportshunt/utils/razorpay_utils.py`

**Contents**:
```python
import razorpay
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class RazorpayManager:
    """
    Manager class for Razorpay operations.
    Handles order creation and payment verification.
    """
    
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    def create_order(self, amount, order_id, notes=None):
        """
        Create a Razorpay order.
        
        Args:
            amount (int): Amount in paise (1 INR = 100 paise)
            order_id (str): Unique order ID from our Order model
            notes (dict): Additional metadata (tournament, category, team info)
        
        Returns:
            dict: Razorpay order response with 'id', 'amount', 'currency'
            
        Raises:
            Exception: If Razorpay API fails
        """
        try:
            order_payload = {
                'amount': amount,  # In paise
                'currency': 'INR',
                'receipt': order_id,
                'notes': notes or {}
            }
            
            order = self.client.order.create(data=order_payload)
            logger.info(f"Razorpay order created: {order['id']} for order_id: {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {str(e)}")
            raise
    
    def verify_payment_signature(self, order_id, payment_id, signature):
        """
        Verify payment signature from Razorpay using SDK utility.
        
        Delegates to Razorpay SDK to ensure compatibility with upstream changes.
        Uses HMAC-SHA256 under the hood (single source of truth).
        
        Args:
            order_id (str): Razorpay order ID
            payment_id (str): Razorpay payment ID
            signature (str): Razorpay signature from frontend
        
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            # Use Razorpay SDK utility for verification (matches SDK version)
            is_valid = self.client.utility.verify_payment_signature(
                {
                    'razorpay_order_id': order_id,
                    'razorpay_payment_id': payment_id,
                    'razorpay_signature': signature
                }
            )
            
            if is_valid:
                logger.info(f"Payment signature verified")
            else:
                logger.warning(f"Invalid payment signature")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return False

# Singleton instance
razorpay_manager = RazorpayManager()
```

---

## Frontend to Backend API Endpoints

### Endpoint 1: Create Order (Initial Request)

**URL**: `POST /api/team-registration/create-order/`  
**Auth**: Required (Bearer token)

**Request Body**:
```json
{
    "tournament_id": 1,
    "category_id": 5,
    "team_name": "Warriors",
    "amount": 5000
}
```

**Response (Success - 201)**:
```json
{
    "order_id": "order_1702934400_001",
    "razorpay_order_id": "order_KA7d8x0TwFNS6Z",
    "amount": 5000,
    "currency": "INR",
    "tournament": {
        "id": 1,
        "name": "Spring Tennis Championship"
    },
    "category": {
        "id": 5,
        "name": "U-19 Men's Singles"
    },
    "team_name": "Warriors",
    "created_at": "2025-12-06T10:30:00Z"
}
```

**Response (Error - 400/500)**:
```json
{
    "error": "payment_order_creation_failed",
    "message": "Unable to initiate payment. Please try again."
}
```

**Response (Error - 404 - Specific)**:
```json
{
    "error": "tournament_not_found",
    "message": "Tournament not found"
}
```

---

### Endpoint 2: Verify Payment Signature & Create Team

**URL**: `POST /api/team-registration/verify-payment/`  
**Auth**: Required (Bearer token)

**Request Body**:
```json
{
    "order_id": "order_1702934400_001",
    "razorpay_payment_id": "pay_KA7d8x0TwFNS6Z",
    "razorpay_signature": "9ef4dffbfd84f1318f6739a3ce19f9d85851857ae648f114332d8401e0949a3d"
}
```

**Response (Success - 200)**:
```json
{
    "status": "payment_verified",
    "message": "Team registered successfully",
    "team_id": 42,
    "team_name": "Warriors",
    "category": "U-19 Men's Singles",
    "tournament": "Spring Tennis Championship",
    "payment_id": "pay_KA7d8x0TwFNS6Z",
    "amount": "5000 INR"
}
```

**Response (Error - 400)**:
```json
{
    "error": "invalid_signature",
    "message": "Payment signature verification failed. Please try again."
}
```

---

## Order Model Enhancement

**Current Model** (`coreApi/models.py`):
```python
class Order(models.Model):
    order_id = models.CharField(max_length=100, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    order_timestamp = models.DateTimeField(auto_now_add=True)
    signature = models.CharField(max_length=255, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    team_instance = models.ForeignKey("organizationApi.Team", on_delete=models.CASCADE, blank=True, null=True)
    team_name = models.CharField(max_length=100)
    category_instance = models.ForeignKey("organizationApi.Category", on_delete=models.CASCADE, blank=True, null=True)
    tournament_instance = models.ForeignKey("organizationApi.Tournament", on_delete=models.CASCADE, blank=True, null=True)
```

**Enhancements to Consider** (Recommended):
```python
class Order(models.Model):
    # Payment Status Choices
    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('completed', 'Payment Completed'),
        ('failed', 'Payment Failed'),
        ('cancelled', 'Payment Cancelled'),
    ]
    
    # Use default id as PK instead of order_id; plays nicer with DRF/admin/relations
    order_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Amount stored in rupees (INR). Multiply by 100 for Razorpay (paise).
    # Conversion happens in views at create_order() call.
    amount = models.IntegerField()
    
    # Payment Details
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    order_timestamp = models.DateTimeField(auto_now_add=True)
    payment_timestamp = models.DateTimeField(blank=True, null=True)
    
    # References to payment context
    team_instance = models.ForeignKey("organizationApi.Team", on_delete=models.CASCADE, blank=True, null=True)
    team_name = models.CharField(max_length=100)
    category_instance = models.ForeignKey("organizationApi.Category", on_delete=models.CASCADE, blank=True, null=True)
    tournament_instance = models.ForeignKey("organizationApi.Tournament", on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.team_name} ({self.payment_status})"
```

---

## Serializers for Payment Endpoints

**Location**: Add to `coreApi/serializers.py`

```python
from rest_framework import serializers
from .models import Order
from organizationApi.models import Tournament, Category

class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating a new Razorpay order"""
    tournament_id = serializers.IntegerField(required=True)
    category_id = serializers.IntegerField(required=True)
    team_name = serializers.CharField(max_length=100, required=True)
    amount = serializers.IntegerField(required=True)  # Amount in rupees
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        if value > 1000000:  # 10 lakhs max
            raise serializers.ValidationError("Amount exceeds maximum limit")
        return value
    
    def validate_tournament_id(self, value):
        if not Tournament.objects.filter(id=value).exists():
            raise serializers.ValidationError("Tournament not found")
        return value
    
    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category not found")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for verifying Razorpay payment"""
    order_id = serializers.CharField(max_length=100, required=True)
    razorpay_payment_id = serializers.CharField(max_length=100, required=True)
    razorpay_signature = serializers.CharField(max_length=255, required=True)


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    class Meta:
        model = Order
        fields = [
            'order_id', 'amount', 'payment_status', 'razorpay_order_id',
            'payment_id', 'signature', 'order_timestamp', 'team_name',
            'tournament_instance', 'category_instance'
        ]
        read_only_fields = ['order_id', 'order_timestamp']
```

---

## View Implementation

**Location**: Add to `coreApi/views.py`

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from sportshunt.utils import login_required_api
from sportshunt.utils.razorpay_utils import razorpay_manager
from organizationApi.models import Tournament, Category
from .models import Order
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@login_required_api
def create_order(request, user=None):
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
    serializer = CreateOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        tournament = Tournament.objects.get(id=serializer.validated_data['tournament_id'])
        category = Category.objects.get(id=serializer.validated_data['category_id'])
        
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
        
        logger.info(f"Order created: {order_id} for user {user.username}")
        
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
        # Log full error server-side with structured fields
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
        # Return generic error to client (no internal details leaked)
        return Response(
            {'error': 'payment_order_creation_failed', 'message': 'Unable to initiate payment. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@login_required_api
def verify_payment(request, user=None):
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
    serializer = VerifyPaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Fetch order from DB
        order = Order.objects.get(order_id=serializer.validated_data['order_id'])
        
        # IDEMPOTENCY GUARD 1: If already completed, return success (handle retries safely)
        if order.payment_status == 'completed':
            logger.info(
                "Payment already verified (idempotent retry)",
                extra={'order_id': order.id, 'user_id': user.id}
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
                extra={'order_id': order.id, 'user_id': user.id}
            )
            return Response(
                {'error': 'invalid_signature', 'message': 'Payment verification failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update Order with payment details
        order.payment_id = serializer.validated_data['razorpay_payment_id']
        order.signature = serializer.validated_data['razorpay_signature']
        order.payment_status = 'completed'
        order.payment_timestamp = datetime.now()
        order.save()
        
        # IDEMPOTENCY GUARD 2: Check if team already created (webhook may have created it)
        if order.team_instance:
            # Team already exists (created by webhook or previous verification)
            team = order.team_instance
            logger.info(
                "Team already exists for order",
                extra={
                    'order_id': order.id,
                    'team_id': team.id,
                    'user_id': user.id
                }
            )
        else:
            # Create Team record only if not already created
            team = Team.objects.create(
                name=order.team_name,
                category=order.category_instance,
                # Add other required fields based on Team model
            )
            order.team_instance = team
            order.save()
            
            logger.info(
                "Payment verified and team created",
                extra={
                    'order_id': order.id,
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
        # Log full error server-side with structured fields
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
        # Return generic error to client (no internal details leaked)
        return Response(
            {'error': 'payment_verification_failed', 'message': 'Payment verification failed. Please contact support if this persists.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

## Webhook Endpoint (NEW)

**Location**: Add to `coreApi/views.py`

```python
from django.views.decorators.csrf import csrf_exempt
import json

@api_view(['POST'])
@csrf_exempt  # Razorpay cannot send CSRF token
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
        # Note: payment.authorized fires if auto_capture=False (manual capture needed)
        #       payment.captured fires when payment is actually captured (final success)
        #       If using auto_capture=True, payment.authorized = payment.captured
        if event_type == 'payment.authorized':
            payment = payload.get('payment', {}).get('entity', {})
            order_data = payload.get('order', {}).get('entity', {})
            
            razorpay_order_id = order_data.get('id')
            razorpay_payment_id = payment.get('id')
            
            # Update order status (authorized = ready to capture or already captured if auto_capture=True)
            order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
            if order:
                order.payment_id = razorpay_payment_id
                # Note: If auto_capture=False, payment is authorized but not yet captured.
                #       Set status to 'authorized' and wait for payment.captured event for final success.
                #       If auto_capture=True, payment is captured; set status to 'completed'.
                # For simplicity, this example assumes auto_capture=True.
                order.payment_status = 'completed'
                order.payment_timestamp = datetime.now()
                order.save()
                
                # Create team if not already created (idempotent)
                if not order.team_instance:
                    team = Team.objects.create(
                        name=order.team_name,
                        category=order.category_instance,
                    )
                    order.team_instance = team
                    order.save()
                    logger.info(
                        "Team created via webhook",
                        extra={'order_id': order.id, 'team_id': team.id}
                    )
        
        elif event_type == 'payment.captured':
            # Final payment success (use this if auto_capture=False)
            payment = payload.get('payment', {}).get('entity', {})
            order_data = payload.get('order', {}).get('entity', {})
            
            razorpay_order_id = order_data.get('id')
            razorpay_payment_id = payment.get('id')
            
            order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
            if order and order.payment_status != 'completed':  # Avoid duplicate processing
                order.payment_id = razorpay_payment_id
                order.payment_status = 'completed'
                order.payment_timestamp = datetime.now()
                order.save()
                
                # Create team if not already created (idempotent)
                if not order.team_instance:
                    team = Team.objects.create(
                        name=order.team_name,
                        category=order.category_instance,
                    )
                    order.team_instance = team
                    order.save()
                    logger.info(
                        "Team created via webhook",
                        extra={'order_id': order.id, 'team_id': team.id}
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
                    extra={'order_id': order.id}
                )
        
        # Return 200 to acknowledge (Razorpay retries if 2xx not received)
        return Response({'status': 'received'}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(
            "Webhook processing failed",
            extra={'error_type': type(e).__name__, 'error_message': str(e)},
            exc_info=True
        )
        # Return 200 anyway to prevent Razorpay retries (log and alert ops)
        return Response({'status': 'received'}, status=status.HTTP_200_OK)
```

**Add webhook signature verification to RazorpayManager**:
```python
def verify_webhook_signature(self, webhook_body, webhook_signature):
    """
    Verify Razorpay webhook signature.
    
    Args:
        webhook_body (bytes): Raw webhook request body
        webhook_signature (str): Signature from X-Razorpay-Signature header
    
    Returns:
        bool: True if signature is valid
    """
    try:
        is_valid = self.client.utility.verify_webhook_signature(
            webhook_body,
            webhook_signature,
            settings.RAZORPAY_WEBHOOK_SECRET
        )
        return is_valid
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        return False
```

---

## URL Routes

**Location**: Add to `coreApi/urls.py`

```python
from django.urls import path
from .views import *

urlpatterns = [
    # ... existing routes ...
    path('team-registration/create-order/', create_order, name='create-order'),
    path('team-registration/verify-payment/', verify_payment, name='verify-payment'),
    path('razorpay/webhook/', razorpay_webhook, name='razorpay-webhook'),
]
```

---

## Security Considerations

### Critical Security Rules

1. **Signature Verification (Server-Side ONLY)**
   - ✅ **ALWAYS** verify Razorpay signature on backend using SDK utility
   - ✅ Never trust payment status from frontend alone
   - ✅ Use HMAC-SHA256 via `client.utility.verify_payment_signature()`
   - ❌ Never verify signature on frontend (private key is exposed)

2. **Key Protection**
   - ✅ Store `RAZORPAY_KEY_SECRET` in environment variables only
   - ✅ Never commit keys to git
   - ✅ Rotate keys regularly in production
   - ❌ Never expose `RAZORPAY_KEY_SECRET` in frontend code, logs, or responses
   - ✅ Only expose `RAZORPAY_KEY_ID` to frontend (it's public)

3. **HTTPS Enforcement**
   - ✅ Payment endpoints must ALWAYS use HTTPS in production
   - ✅ Redirect HTTP → HTTPS
   - ✅ Use HSTS headers
   - ❌ Never test payments over HTTP (even on dev servers)

4. **CORS & Cross-Origin Security**
   - ✅ Whitelist payment endpoints in `CORS_ALLOWED_ORIGINS`
   - ✅ Use `X-Requested-With` header validation
   - ✅ Validate origin in webhook verification
   - ❌ Don't use `CORS_ALLOW_ALL_ORIGINS = True` for payment routes

5. **Rate Limiting & DDoS Protection**
   - ✅ Implement rate limiting on `/create-order/` (prevent order spam)
   - ✅ Implement rate limiting on `/verify-payment/` (prevent verification spam)
   - ✅ Consider: 5-10 requests/min per user per endpoint
   - ✅ Use Django Ratelimit or similar package

6. **Logging & Audit Trail**
   - ✅ Log all payment attempts with order_id, user_id, timestamp
   - ✅ Log all verification successes and failures
   - ✅ Store logs separately (not accessible via web)
   - ✅ Never log full payment_id or signature
   - ❌ Don't log customer card details or sensitive PII

7. **Webhook Security**
   - ✅ Verify webhook signature before processing
   - ✅ Check webhook origin header
   - ✅ Idempotently process webhook (no duplicate team creation)
   - ✅ Return 200 OK immediately to Razorpay (process async if needed)
   - ✅ Whitelist Razorpay IP ranges if possible
   - ❌ Don't trust webhook data without signature verification

8. **PCI Compliance**
   - ✅ Razorpay handles PCI compliance (never store card data)
   - ✅ Order model stores order_id, amount, payment_id only
   - ✅ Never store card number, CVV, or expiry
   - ✅ Ensure HTTPS + TLS 1.2+

### Implementation Checklist
```
- [ ] All payment endpoints require HTTPS in production
- [ ] RAZORPAY_KEY_SECRET stored in .env (not in code)
- [ ] Webhook signature verified before processing
- [ ] Rate limiting configured on payment endpoints
- [ ] CORS whitelist updated for payment routes
- [ ] Logging configured with structured fields (order_id, user_id)
- [ ] No sensitive data in error responses
- [ ] Signature verification uses SDK utility
- [ ] Production keys (live) separate from sandbox (test)
- [ ] Security audit before going live
```

---

### Step 1: Install Razorpay Package
```bash
npm install razorpay-checkout
```

### Step 2: Create Order
```javascript
const createOrder = async (tournamentId, categoryId, teamName, amount) => {
  const response = await fetch('/api/team-registration/create-order/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({
      tournament_id: tournamentId,
      category_id: categoryId,
      team_name: teamName,
      amount: amount
    })
  });
  
  return response.json();
};
```

### Step 3: Initialize Razorpay Checkout (with Error Handling)
```javascript
const handlePayment = async (orderData) => {
  const options = {
    key: process.env.REACT_APP_RAZORPAY_KEY,
    amount: orderData.amount * 100,  // Convert to paise
    currency: 'INR',
    name: 'SportsHunt',
    description: `${orderData.tournament} - ${orderData.category}`,
    order_id: orderData.razorpay_order_id,
    handler: async (response) => {
      try {
        setLoading(true);
        
        // Call verification endpoint with error handling
        const verificationResponse = await verifyPayment(
          orderData.order_id,
          response.razorpay_payment_id,
          response.razorpay_signature
        );
        
        if (verificationResponse.status === 'payment_verified') {
          showSuccessToast('Team registered successfully!');
          navigate('/dashboard');
        } else if (verificationResponse.is_duplicate) {
          showInfoToast('Payment already verified');
          navigate('/dashboard');
        } else {
          showErrorToast(verificationResponse.message || 'Verification failed');
          setShowRetryButton(true);
        }
      } catch (error) {
        logger.error('Verification failed', error);
        showErrorToast('Payment verification failed. Retrying...');
        setShowRetryButton(true);
        // Optional: Auto-retry after delay
        setTimeout(() => handleRetry(orderData), 3000);
      } finally {
        setLoading(false);
      }
    },
    onDismiss: () => {
      logger.warn('Payment cancelled by user');
      showWarningToast('Payment cancelled. You can retry anytime.');
    },
    prefill: {
      email: userEmail,
      contact: userPhone
    }
  };
  
  try {
    setLoading(true);
    const rzp = new window.Razorpay(options);
    rzp.open();
  } catch (error) {
    logger.error('Failed to open payment gateway', error);
    showErrorToast('Payment gateway unavailable. Please try again.');
    setLoading(false);
  }
};

// NEW: Retry verification handler
const handleRetry = async (orderData) => {
  try {
    setLoading(true);
    // Re-attempt verification (webhook may have processed it)
    const result = await verifyPayment(
      orderData.order_id,
      orderData.razorpay_payment_id,
      orderData.razorpay_signature
    );
    
    if (result.status === 'payment_verified' || result.is_duplicate) {
      showSuccessToast('Payment verified!');
      navigate('/dashboard');
    } else {
      showErrorToast('Retry failed. Contact support.');
    }
  } catch (error) {
    logger.error('Retry failed', error);
    showErrorToast('Retry failed. Contact support with order ID: ' + orderData.order_id);
  } finally {
    setLoading(false);
    setShowRetryButton(false);
  }
};
```

### Step 4: Verify Payment (with Comprehensive Error Handling)
```javascript
const verifyPayment = async (orderId, paymentId, signature) => {
  try {
    const response = await fetch('/api/team-registration/verify-payment/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        order_id: orderId,
        razorpay_payment_id: paymentId,
        razorpay_signature: signature
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      logger.warn('Verification returned error status', { status: response.status, error: errorData.error });
      
      // Handle specific error codes
      if (errorData.error === 'invalid_signature') {
        throw new Error('Payment signature verification failed. Please try again.');
      } else if (errorData.error === 'order_not_found') {
        throw new Error('Order not found. Please create order again.');
      }
      throw new Error(errorData.message || 'Verification failed');
    }
    
    return await response.json();
  } catch (error) {
    logger.error('Verify payment error', { error: error.message });
    throw error;
  }
};
```

---

## Environment Variables

**.env file** (Backend):
```
# Razorpay API Credentials (from Dashboard → Settings → API Keys)
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxx

# Razorpay Webhook Secret (from Dashboard → Settings → Webhooks)
RAZORPAY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Frontend URL for CORS
FRONTEND_URL=https://yourdomain.com
```

**.env file** (Frontend - React):
```
# Razorpay public key (safe to expose to frontend)
REACT_APP_RAZORPAY_KEY=rzp_live_xxxxxxxxxxxxx

# Backend API endpoint
REACT_APP_API_URL=https://yourdomain.com/api
```

### Key Safety Rules

| Key | Environment | Exposed to Frontend? | Location |
|-----|-------------|----------------------|----------|
| `RAZORPAY_KEY_ID` | Both | ✅ Yes (public) | .env |
| `RAZORPAY_KEY_SECRET` | Backend only | ❌ NO (private) | .env (protected) |
| `RAZORPAY_WEBHOOK_SECRET` | Backend only | ❌ NO (private) | .env (protected) |

**Never do this:**
```javascript
// ❌ BAD: Exposing secret in frontend
const secret = process.env.REACT_APP_RAZORPAY_SECRET; // WRONG!
```

**Do this instead:**
```javascript
// ✅ GOOD: Only public key in frontend
const keyId = process.env.REACT_APP_RAZORPAY_KEY;
```

---

## Error Handling & Troubleshooting

## Error Response Codes

| HTTP Status | Error Code | Cause | User Message | Fix |
|-------------|-----------|-------|--------------|-----|
| 400 | `invalid_signature` | Payment signature doesn't match | "Payment verification failed. Please try again." | Retry payment; if persists, contact support |
| 400 | `category_registration_closed` | Registration deadline passed | "Registration closed for this category" | Choose different category |
| 404 | `tournament_not_found` | Tournament ID invalid | "Tournament not found" | Refresh page, select valid tournament |
| 404 | `category_not_found` | Category ID invalid | "Category not found" | Refresh page, select valid category |
| 404 | `order_not_found` | Order ID doesn't exist | "Order not found" | Restart payment flow |
| 500 | `payment_order_creation_failed` | Razorpay API error or DB issue | "Unable to initiate payment. Please try again." | Retry; check server logs for details |
| 500 | `payment_verification_failed` | Backend verification error | "Payment verification failed. Please contact support if this persists." | Contact support with order_id |

### Common Issues & Solutions

| Issue | Symptom | Debug Steps |
|-------|---------|-------------|
| **Invalid Signature** | Verify endpoint returns 400 | Check: order_id format, razorpay_order_id in DB, signature matches payload |
| **Webhook Not Firing** | Order status stays 'pending' | Check: webhook URL registered in Dashboard, endpoint accepts POST, signature verification passes |
| **Order Creation Fails** | 500 error on create endpoint | Check: env vars set, Razorpay creds valid, category registration_status=True, server logs |
| **Team Not Created** | Order verified but team_instance null | Check: verify_payment view completes, Team model required fields, database constraints |
| **CORS Error on Frontend** | Payment endpoints blocked by browser | Check: CORS_ALLOWED_ORIGINS includes frontend URL, headers sent correctly |
| **Rate Limiting Blocks Retry** | Too many requests error | Check: rate limit config, user wait time before retry, implement exponential backoff |

### Debug Checklist

**For Create Order Failures:**
```
- [ ] Check RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in env
- [ ] Verify tournament_id exists: SELECT * FROM organizationApi_tournament WHERE id=X;
- [ ] Verify category_id exists: SELECT * FROM organizationApi_category WHERE id=X;
- [ ] Verify category.registration_status = True (or 1)
- [ ] Check server logs for full error trace (grep for order_id)
- [ ] Test Razorpay SDK connection: razorpay.Client(...).order.create(...)
```

**For Verify Payment Failures:**
```
- [ ] Check order exists: SELECT * FROM coreApi_order WHERE order_id='xxx';
- [ ] Verify razorpay_order_id matches: SELECT razorpay_order_id FROM coreApi_order WHERE order_id='xxx';
- [ ] Check signature format (256 char hex string)
- [ ] Verify RAZORPAY_KEY_SECRET matches Razorpay account
- [ ] Test signature manually: client.utility.verify_payment_signature(...)
- [ ] Check if order already completed (is_duplicate guard)
```

**For Webhook Issues:**
```
- [ ] Verify webhook URL in Razorpay Dashboard settings
- [ ] Check webhook secret in .env matches Dashboard
- [ ] Send test webhook from Dashboard → check backend logs
- [ ] Verify X-Razorpay-Signature header present
- [ ] Check webhook endpoint returns 200 OK
- [ ] Verify idempotency: send same webhook twice, check no duplicate teams
```

---

## Database Migrations

After updating the Order model:

```bash
python manage.py makemigrations coreApi
python manage.py migrate coreApi
```

---

## Webhook Configuration (Production Readiness)

### Webhook URL Setup (Razorpay Dashboard)

1. **Navigate to Settings → Webhooks**
2. **Add Webhook Endpoint**:
   - URL: `https://yourdomain.com/api/razorpay/webhook/`
   - Events to listen for:
     - `payment.authorized` - Payment successful
     - `payment.failed` - Payment failed
     - `payment.captured` - Payment captured (optional)

3. **Enable webhook delivery** in Dashboard
4. **Add webhook secret** to environment variables:
   ```
   RAZORPAY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
   ```

### Webhook Event Types

| Event | Payload | Action | Priority | Note |
|-------|---------|--------|----------|------|
| `payment.authorized` | payment_id, order_id, amount | Update order status (if auto_capture=True, treat as completed) | HIGH | Fires when auth succeeds; if auto_capture=False, wait for payment.captured |
| `payment.captured` | payment_id, order_id | Update order status → completed, create team | HIGH | Final success event if auto_capture=False; use this as authoritative signal |
| `payment.failed` | payment_id, order_id, reason | Update order status → failed | HIGH | Payment explicitly failed; mark order and notify user |

### Webhook Flow (Offline Safety)

```
Scenario: Frontend network error during verify_payment call
├─ Payment succeeded on Razorpay
├─ Frontend never received success response
├─ Razorpay sends webhook (payment.authorized)
├─ Backend processes webhook
├─ Team created via webhook
├─ User retries verify_payment
├─ Backend returns: "already verified (is_duplicate=true)"
└─ User sees success (idempotent)
```

### Testing Webhooks (Sandbox)

1. **Send test webhook from Razorpay Dashboard**:
   - Navigate to Webhooks section
   - Click "Send Event" on payment.authorized
   - Check backend logs for processing

2. **Verify webhook processing**:
   - Check Order.payment_status updated to 'completed'
   - Check Team record created
   - Verify logs contain order_id and team_id

3. **Test retry logic**:
   - Send same webhook twice
   - Verify team created only once (idempotency)

---

### Test Credentials (Sandbox)
```
Key ID: rzp_test_1Aa00000000001
Key Secret: (provided by Razorpay)
```

### Test Payment Cards
- **Success**: 4111 1111 1111 1111
- **Failure**: 4444 3333 2222 1111

### Test Webhook
Use Razorpay Dashboard to send test webhooks for payment.completed, payment.failed events

---

## Checklist

### Backend Setup
- [ ] Install `razorpay>=1.4.1` package in requirements.txt
- [ ] Add `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` to `.env`
- [ ] Update `sportshunt/conf/dev.py` and `prod.py` with Razorpay config
- [ ] Validate env vars on app startup (raise error if missing)

### Database Layer
- [ ] Update Order model: remove duplicate fields, add payment_status choices
- [ ] Run `python manage.py makemigrations coreApi`
- [ ] Run `python manage.py migrate coreApi`
- [ ] Verify migration rollback works (test rollback to previous state)

### Business Logic Layer
- [ ] Create `sportshunt/utils/razorpay_utils.py` with RazorpayManager
- [ ] Implement `create_order()` method using SDK
- [ ] Implement `verify_payment_signature()` using SDK utility
- [ ] Implement `verify_webhook_signature()` for webhook verification
- [ ] Add structured logging with extra fields
- [ ] Test utility functions in isolation

### View Layer
- [ ] Create `create_order()` view in `coreApi/views.py`
- [ ] Create `verify_payment()` view with idempotency guards
- [ ] Create `razorpay_webhook()` view (csrf_exempt decorator)
- [ ] Add error handling (generic client messages, full server logs)
- [ ] Add serializers (CreateOrderSerializer, VerifyPaymentSerializer)
- [ ] Test views with mock Razorpay responses

### URL Routing
- [ ] Add routes to `coreApi/urls.py`:
  - `path('team-registration/create-order/', create_order)`
  - `path('team-registration/verify-payment/', verify_payment)`
  - `path('razorpay/webhook/', razorpay_webhook)`

### Frontend Integration (React)
- [ ] Install `razorpay-checkout` npm package
- [ ] Create order function with error handling
- [ ] Implement Razorpay checkout initialization
- [ ] Add payment handler with try/catch
- [ ] Add retry mechanism for verification failures
- [ ] Add UI states: loading, success, error, retry
- [ ] Implement error toasts/snackbars

### Infrastructure & Security
- [ ] Configure CORS: add payment endpoints to whitelist
- [ ] Enable HTTPS on production (redirect HTTP → HTTPS)
- [ ] Setup rate limiting: `django-ratelimit` or similar
  - 5-10 requests/min on `/create-order/`
  - 5-10 requests/min on `/verify-payment/`
- [ ] Configure webhook URL in Razorpay Dashboard
  - `https://yourdomain.com/api/razorpay/webhook/`
- [ ] Whitelist Razorpay IPs if behind firewall
- [ ] Setup log rotation (prevent disk overflow)
- [ ] Configure error alerting (e.g., Sentry for 500s)

### Testing
- [ ] Unit tests for RazorpayManager methods
- [ ] Unit tests for view error cases
- [ ] Integration tests with mock Razorpay SDK
- [ ] Sandbox test with Razorpay test credentials
  - Test card: 4111 1111 1111 1111 (success)
  - Test card: 4444 3333 2222 1111 (failure)
- [ ] Test webhook delivery from Razorpay Dashboard
- [ ] Test payment flow end-to-end:
  - Create order
  - Complete payment
  - Verify signature
  - Verify team created

### Monitoring & Observability
- [ ] Setup structured logging aggregation (ELK, Datadog, etc)
- [ ] Configure alerts for payment failures
- [ ] Monitor webhook delivery latency
- [ ] Track order creation/completion metrics
- [ ] Dashboard for payment health

### Production Deployment
- [ ] Swap sandbox keys → live keys in `.env`
- [ ] Enable webhook delivery in Razorpay Dashboard
- [ ] Test end-to-end with live keys (small amount)
- [ ] Monitor logs for issues
- [ ] Document runbook for payment troubleshooting
- [ ] Backup webhook log (separate from app logs)
- [ ] Schedule key rotation (e.g., quarterly)

### Post-Launch
- [ ] Document API responses in Postman collection
- [ ] Create customer-facing payment troubleshooting guide
- [ ] Monitor refund requests (not covered in this doc)
- [ ] Plan for refund integration if needed
- [ ] Setup auto-reconciliation job (optional)

---

## References

- [Razorpay Python SDK Documentation](https://razorpay.com/docs/payment-gateway/sdk/python/)
- [Razorpay Signature Verification](https://razorpay.com/docs/payment-gateway/payments/payment-verification/)
- [Razorpay Checkout Widget Integration](https://razorpay.com/docs/payment-gateway/web-integration/web-standard/)
- [Razorpay Webhooks](https://razorpay.com/docs/webhooks/)
- [Razorpay Test Credentials](https://razorpay.com/docs/payments/payment-gateway/test-cards/)
- [Razorpay API Reference](https://razorpay.com/api-reference/)
- [Django CSRF Exemption](https://docs.djangoproject.com/en/5.0/ref/csrf/#django.views.decorators.csrf.csrf_exempt)
- [Django Ratelimit Package](https://github.com/view-flow/django-ratelimit/)

---

## Status & Next Steps

**Current Implementation Status**: Not yet implemented  
**Priority**: High  
**Complexity**: Medium (3-5 days for full implementation)  
**Dependencies**: razorpay package, environment variables, Razorpay account

### Implementation Phases

**Phase 1: Backend Setup** (1-2 days)
- Install package, setup env vars
- Update Order model, run migrations
- Create RazorpayManager utility
- Implement create_order and verify_payment views

**Phase 2: Frontend Integration** (1-2 days)
- Setup Razorpay checkout
- Add error handling and retry logic
- Test with sandbox credentials

**Phase 3: Webhook & Production** (1 day)
- Implement webhook endpoint
- Configure webhook in Razorpay Dashboard
- Setup rate limiting and CORS
- Security audit before go-live

**Phase 4: Testing & Monitoring** (1 day)
- End-to-end testing
- Load testing
- Observability setup (logs, alerts)
- Runbook documentation

### Go-Live Checklist
- [ ] Code reviewed and approved
- [ ] All tests passing (unit + integration + E2E)
- [ ] Security audit completed
- [ ] Sandbox testing verified
- [ ] Rate limiting configured
- [ ] Logging/monitoring setup
- [ ] Documentation updated
- [ ] Team trained on troubleshooting
- [ ] Swap test keys → live keys
- [ ] Monitor first 24 hours closely

### Known Limitations (Future Work)
- Refund integration (not covered in this phase)
- Partial payment support (future)
- Payment plan/subscription support (future)
- Multi-currency support (future)
- Settlement reconciliation job (future)
