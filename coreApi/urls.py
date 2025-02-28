from django.urls import path
from .views import *
from sportshunt.utils import *

urlpatterns = [
    path('', index),
    path("login/", login_view, name="login"),
    path("login/handler/", login_handler, name="login_handler"),
    path("logout/", logout_view, name="logout"),
    path("logout/handler/", logout_handler, name="logout_handler"),
    path("upcoming-past_tournaments/", tournament_list, name="tournament_list"),
    path('profile/', profile_api, name='profile_api'),
    path('tournament/<int:tournament_id>/', tournament_detail_api, name='tournament_detail_api'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/', category_detail_api, name='category_detail_api'),
]

app_name = 'core'