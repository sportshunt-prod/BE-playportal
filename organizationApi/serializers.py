from rest_framework import serializers
from organizationApi.models import Organization, Sport
from datetime import datetime
import re
from organizationApi.models import *
import math
from django.db import transaction

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'admin', 'mail', 'ph_number']
        read_only_fields = ['id', 'admin']  # Make admin read-only
    
    def validate(self, data):
        user = self.context.get('request').user
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


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'category']
        read_only_fields = ['id']
    
    def validate_category(self, category):
        if not category.registration_status:
            raise serializers.ValidationError("Registration is closed for this category.")
        return category


class FixtureSerializer(serializers.Serializer):
    fixtureType = serializers.ChoiceField(choices=['KO', 'RR'], required=True)
    noOfSets = serializers.IntegerField(min_value=1, required=False, default=3)
    pointsToWin = serializers.IntegerField(min_value=1, required=False, default=15)
    noOfRounds = serializers.IntegerField(min_value=1, required=False, default=1)
    
    def validate(self, data):
        fixture_type = data.get('fixtureType')
        
        # Validate required fields for RR fixture type
        if fixture_type == 'RR':
            if 'pointsToWin' not in data:
                data['pointsToWin'] = 15  # Default value
            if 'noOfRounds' not in data:
                data['noOfRounds'] = 1    # Default value
            if 'noOfSets' not in data:
                data['noOfSets'] = 3      # Default value
                
        return data
    
    def create_fixture(self, category_instance):
        """
        Create fixture for a category based on validated data
        """
        try:
            with transaction.atomic():
                teams = category_instance.teams.all()
                
                if teams.count() == 1:
                    category_instance.winner = teams.first()
                    category_instance.save()
                    raise serializers.ValidationError(
                        {"teams": "Only one team in the category, so they won by default"}
                    )
                
                fixture_type = self.validated_data.get('fixtureType')
                fixture_instance = Fixture.objects.create(fixtureType=fixture_type, category=category_instance)
                
                if fixture_type == 'KO':
                    ko_instance = Knockout.objects.create(category=category_instance)
                    ko_instance.bracket_teams.set(teams)
                    no_teams = teams.count()
                    cur_lvl = math.ceil(math.log2(no_teams))
                    ko_instance.ko_stage = cur_lvl
                    ko_instance.save()

                    fixture_instance.content_object = ko_instance
                    fixture_instance.save()
                    category_instance.fixture = fixture_instance
                    category_instance.save()

                elif fixture_type == 'RR':
                    points_to_win = self.validated_data.get('pointsToWin')
                    no_of_rounds = self.validated_data.get('noOfRounds')
                    no_sets = self.validated_data.get('noOfSets')
                    
                    category_instance.required_points = points_to_win
                    category_instance.max_sets = no_sets
                    rr_instance = RoundRobin.objects.create(
                        category=category_instance, 
                        rounds=no_of_rounds,
                    )
                    
                    rr_teams = []
                    for team in teams:
                        rr_teams.append(RR_Team(team=team, round_robin=rr_instance))
                    
                    # Use bulk_create for better performance
                    created_rr_teams = RR_Team.objects.bulk_create(rr_teams)
                    rr_instance.rr_teams.set(created_rr_teams)
                    rr_instance.schedule_matches()    
                    fixture_instance.content_object = rr_instance
                    fixture_instance.save()
                    
                    category_instance.fixture = fixture_instance
                    category_instance.save()
                    rr_instance.save()
                
                return fixture_instance
                
        except serializers.ValidationError as e:
            raise e
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        

class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'details', 'price', 'registration_status']


class SportDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ['id', 'name', 'scoring_type']


class TournamentDetailSerializer(serializers.ModelSerializer):
    categories = CategoryDetailSerializer(many=True, read_only=True)
    sport = SportDetailSerializer(read_only=True)
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'details', 'organization', 'start_date', 'end_date', 'venue_address', 'venue_link', 'ph_number', 'sport', 'categories']


class CourtSerializer(serializers.ModelSerializer):
    tournament = serializers.IntegerField(source='tournament.id', read_only=True)
    upcoming_matches_count = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    current_match = serializers.SerializerMethodField()
    upcoming_matches = serializers.SerializerMethodField()

    class Meta:
        model = Court
        fields = [
            'id', 'name', 'tournament', 'current_match',
            'upcoming_matches_count', 'upcoming_matches', 'is_available'
        ]
        read_only_fields = ['id', 'tournament', 'current_match', 'upcoming_matches_count', 'upcoming_matches', 'is_available']

    def get_upcoming_matches_count(self, obj):
        return obj.upcoming_matches.count()

    def get_is_available(self, obj):
        return obj.current_match is None

    def get_current_match(self, obj):
        cm = obj.current_match
        if not cm:
            return None
        return {
            'id': cm.id,
            'team1_name': cm.team1.name if cm.team1 else None,
            'team2_name': cm.team2.name if cm.team2 else None,
            'category_name': cm.category.name if cm.category else None,
            'stage': getattr(cm, 'stage_number', None),
            'match_number': getattr(cm, 'match_number', None)
        }

    def get_upcoming_matches(self, obj):
        # Only include detailed upcoming matches for detail view
        # Check if this is a detail view by looking at context
        include_details = self.context.get('include_upcoming_details', False)
        
        if not include_details:
            return []
            
        upcoming_matches = []
        for idx, match in enumerate(obj.upcoming_matches.all().order_by('id'), 1):
            upcoming_matches.append({
                'id': match.id,
                'queue_position': idx,
                'team1_name': match.team1.name if match.team1 else 'BYE',
                'team2_name': match.team2.name if match.team2 else 'BYE',
                'category_name': match.category.name,
                'stage': getattr(match, 'stage_number', None),
                'match_number': getattr(match, 'match_number', None)
            })
        return upcoming_matches


class CourtCreateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty")

        # Validate uniqueness per tournament
        tournament_id = self.context.get('tournament_id')
        instance = self.instance
        qs = Court.objects.filter(tournament_id=tournament_id, name__iexact=value)
        if instance is not None:
            qs = qs.exclude(id=instance.id)
        if qs.exists():
            raise serializers.ValidationError("Court with this name already exists in this tournament")
        return value

    def create(self, validated_data):
        tournament_id = self.context.get('tournament_id')
        tournament = Tournament.objects.get(id=tournament_id)
        return Court.objects.create(name=validated_data['name'], tournament=tournament)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance