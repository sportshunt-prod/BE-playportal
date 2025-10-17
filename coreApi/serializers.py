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
