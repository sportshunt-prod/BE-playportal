from django.urls import path
from organizationApi import views

urlpatterns = [
    path('organization/create/', views.create_organization, name='create-organization'),
    path('tournament/create/', views.create_tournament, name='create-tournament'),
    path('tournament/<int:tournament_id>/category/create/', views.create_category, name='create-category'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/toggle-registration/', views.toggle_registration, name='toggle-registration'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/team/create/', views.create_team, name='create-team'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/fixture/create/', views.create_fixture, name='create-fixture'),
]

app_name = 'org'