from rest_framework import serializers
from organizationApi.models import Organization
from datetime import datetime
import re
from organizationApi.models import *

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'admin', 'mail', 'ph_number']
        read_only_fields = ['id']
    
    def validate(self, data):
        # Get the user from the context
        user = self.context.get('request').user
        
        # Check if user already has an organization
        if Organization.objects.filter(admin=user).exists():
            raise serializers.ValidationError("You already have an organization. A user can only have one organization")
        
        return data

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name cannot be empty")
        if Organization.objects.filter(name=value).exists():
            raise serializers.ValidationError("Organization with this name already exists")
        return value
    
    def validate_mail(self, value):
        if not value:
            raise serializers.ValidationError("Email cannot be empty")
        return value
    
    def validate_ph_number(self, value):
        if not value:
            raise serializers.ValidationError("Phone number cannot be empty")
        if len(value) != 10:
            raise serializers.ValidationError("Phone number should be 10 digits")
        if not value.isdigit():
            raise serializers.ValidationError("Phone number should contain only digits")
        return value


class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'details', 'organization', 'start_date', 'end_date', 
                    'venue_address', 'venue_link', 'ph_number', 'sport']
        read_only_fields = ['id']
    
    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name cannot be empty")
        return value

    def validate_details(self, value):
        if not value:
            raise serializers.ValidationError("Details cannot be empty")
        return value
    
    def validate_start_date(self, value):
        if not value:
            raise serializers.ValidationError("Start date cannot be empty")
        
        today = datetime.now().date()
        if value < today:
            raise serializers.ValidationError("Start date cannot be in the past")
        return value
    
    def validate_end_date(self, value):
        if not value:
            raise serializers.ValidationError("End date cannot be empty")
        
        start_date = self.initial_data.get('start_date')
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if value < start_date:
                    raise serializers.ValidationError("End date cannot be before start date")
            except (ValueError, TypeError):
                # Start date validation will handle this error
                pass
        
        if value < datetime.now().date():
            raise serializers.ValidationError("End date cannot be in the past")
        
        return value
    
    def validate_venue_address(self, value):
        if not value:
            raise serializers.ValidationError("Venue address cannot be empty")
        return value
    
    def validate_venue_link(self, value):
        if not value:
            return value  # Optional field
        
        google_maps_regex = r'^https?:\/\/(?:www\.|maps\.app\.)?(?:google\.com\/maps\/|goo\.gl\/\S*)$'
        if not re.match(google_maps_regex, value):
            raise serializers.ValidationError('Invalid Google Maps link')
        return value
    
    def validate_sport(self, value):
        if not Sport.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Selected sport does not exist")
        return value
    
    def create(self, validated_data):
        user = self.context.get('request').user
        
        try:
            org_instance = Organization.objects.get(admin=user)
        except Organization.DoesNotExist:
            raise serializers.ValidationError("You don't have an organization to create tournaments")
        
        validated_data['organization'] = org_instance
        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    tournament_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'details', 'price', 'tournament_id', 'registration_status']
        read_only_fields = ['id', 'registration_status']
    
    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name cannot be empty")
        
        if value == "new_category": # url issue 
            raise serializers.ValidationError("Invalid category name")
        
        tournament_id = self.initial_data.get('tournament_id')
        if not tournament_id:
            raise serializers.ValidationError("Tournament ID is required")
        
        if Category.objects.filter(name=value, tournament_id=tournament_id).exists():
            raise serializers.ValidationError("Category with this name already exists in the tournament")
        return value
    
    def validate_details(self, value):
        if not value:
            raise serializers.ValidationError("Details cannot be empty")
        return value
    
    def validate_price(self, value):
        if not value:
            raise serializers.ValidationError("Price cannot be empty")
        try:
            price = float(value)
            if price < 0:
                raise serializers.ValidationError("Price cannot be negative")
        except ValueError:
            raise serializers.ValidationError("Invalid price format")
        return value
    
    def validate_tournament_id(self, value):
        try:
            tournament = Tournament.objects.get(id=value)
            # Check if user is the admin of the organization that owns this tournament
            user = self.context.get('request').user
            if tournament.organization.admin != user:
                raise serializers.ValidationError("You are not authorized to create categories for this tournament")
            return value
        except Tournament.DoesNotExist:
            raise serializers.ValidationError("Tournament not found")
    
    def create(self, validated_data):
        tournament_id = validated_data.pop('tournament_id')
        tournament = Tournament.objects.get(id=tournament_id)
        
        category = Category.objects.create(
            **validated_data,
            tournament=tournament,
            registration_status=True
        )
        
        return category