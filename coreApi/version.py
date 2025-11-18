"""
Version and API information endpoint.
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
import django


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """
    API information and version endpoint.
    
    Returns API version, Django version, and basic API information.
    
    GET /api/info/
    """
    return JsonResponse({
        'api_name': 'PlayPortal Backend API',
        'api_version': '1.0.0',
        'django_version': django.get_version(),
        'status': 'operational',
        'endpoints': {
            'health': '/health/',
            'health_detailed': '/health/detailed/',
            'health_readiness': '/health/readiness/',
            'health_liveness': '/health/liveness/',
            'authentication': '/auth/',
            'sports': '/sports/',
            'tournaments': '/upcoming-past_tournaments/',
        }
    }, status=status.HTTP_200_OK)



