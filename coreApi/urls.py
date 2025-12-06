from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import *

urlpatterns = [
    path('auth/check/', index, name='auth_check'),
    path('auth/register/', register_api, name='register'),
    path('auth/login/', login_api, name='login'),
    path('auth/google/', google_auth_api, name='google_auth'),
    path('auth/logout/', logout_view, name='logout'),
    path('sports/', sports_list_api, name='sports_list'),
    path('upcoming-past_tournaments/', tournament_list, name='tournament_list'),
    path('profile/', profile_api, name='profile_api'),
    path('tournament/<int:tournament_id>/', tournament_detail_api, name='tournament_detail_api'),
    path('tournament/<int:tournament_id>/category/<int:category_id>/', category_detail_api, name='category_detail_api'),
    # Razorpay Payment Routes
    path('team-registration/create-order/', create_order, name='create-order'),
    path('team-registration/verify-payment/', verify_payment, name='verify-payment'),
    path('razorpay/webhook/', csrf_exempt(razorpay_webhook), name='razorpay-webhook'),
]

app_name = 'core'