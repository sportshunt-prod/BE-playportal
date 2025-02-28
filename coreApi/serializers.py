from rest_framework import serializers
from django.contrib.auth.models import User
from organizationApi.models import Tournament, Organization, Category

class UserProfileSerializer(serializers.ModelSerializer):
    auth0_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email','is_organizer', 'auth0_data']

    def get_auth0_data(self, obj):
        try:
            auth0_user = obj.social_auth.get(provider="auth0")
            return {
                'uid': auth0_user.uid,
                'extra_data': auth0_user.extra_data
            }
        except:
            return None

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

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
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Tournament
        fields = '__all__'
