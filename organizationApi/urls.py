from django.urls import path
from organizationApi.views import *

urlpatterns = [
    path('create/org/', create_organization, name='create_organization'),
    path('create/tournament/', create_tournament, name='create_tournament'),
    path('create/tournament/<int:tournament_id>/category/', create_category, name='create_category'),
    
]

app_name = 'org'