from django.urls import path
from organizationApi import views

urlpatterns = [
    path('org_auth/', views.index, name='index'),
    path('create/', views.create_organization, name='create-organization'),
    path('dashboard/', views.org_dashboard, name='my-tournaments'),
    path('tournament/create/', views.create_tournament, name='create-tournament'),
    path('tournament/<int:tournament_id>/', views.tournament_details, name='tournament-details'),
    path('tournament/<int:tournament_id>/category/create/', views.create_category, name='create-category'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/toggle-registration/', views.toggle_registration, name='toggle-registration'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/team/create/', views.register_team, name='create-team'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/fixture/create/', views.create_fixture, name='create-fixture'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/create_ko_matches/', views.create_ko_matches, name='create-ko-match'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/schedule_match/', views.schedule_match, name='schedule-match'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/update_score/', views.update_score, name='update-score'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/fixture/details/', views.get_fixture_details, name='fixture-details'),
    # Courts
    path('tournament/<int:tournament_id>/courts/', views.list_courts, name='courts-list'),
    path('tournament/<int:tournament_id>/new_courts/', views.create_court, name='court-create'),
    path('courts/<int:court_id>/', views.court_detail, name='court-detail'),
]

app_name = 'org'