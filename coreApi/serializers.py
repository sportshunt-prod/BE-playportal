from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from coreApi.models import User
from organizationApi.models import Tournament, Organization, Category


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True, min_length=3, max_length=150)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError("User with this email already exists")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise ValidationError("Username already taken")
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise ValidationError({"password_confirm": "Passwords do not match"})
        
        # Django password validation
        try:
            validate_password(data['password'])
        except DjangoValidationError as e:
            raise ValidationError({"password": list(e.messages)})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class GoogleAuthSerializer(serializers.Serializer):
    credential = serializers.CharField(required=True)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_organizer']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        depth = 1

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['name']

class TournamentListSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()
    
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'organization', 'start_date', 'end_date', 
                 'venue_address', 'completed', 'start_month', 'start_day_date', 
                 'card_details', 'end_date_']
    
class TournamentDetailSerializer(serializers.ModelSerializer):
    
    organization = OrganizationSerializer()
    categories = CategorySerializer(many=True, read_only=True)
    sport = serializers.CharField(source='sport.name', read_only=True)

    class Meta:
        model = Tournament
        fields = '__all__'


# Payment Serializers for Razorpay Integration

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
        from coreApi.models import Order
        model = Order
        fields = [
            'order_id', 'amount', 'payment_status', 'razorpay_order_id',
            'payment_id', 'signature', 'order_timestamp', 'team_name',
            'tournament_instance', 'category_instance'
        ]
        read_only_fields = ['order_id', 'order_timestamp']
