"""
Health check endpoints for production monitoring.
"""
from django.db import connection
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
import os
from pathlib import Path


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint.
    
    Returns 200 OK if the service is running.
    Useful for load balancers and monitoring tools.
    
    GET /health/
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'playportal-backend'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_detailed(request):
    """
    Detailed health check endpoint with system diagnostics.
    
    Checks:
    - Database connectivity
    - Static files availability
    - Basic system health
    
    GET /health/detailed/
    """
    health_status = {
        'status': 'healthy',
        'service': 'playportal-backend',
        'checks': {}
    }
    
    overall_healthy = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        overall_healthy = False
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Static files check
    try:
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root:
            static_path = Path(static_root)
            if static_path.exists():
                health_status['checks']['static_files'] = {
                    'status': 'healthy',
                    'message': 'Static files directory exists',
                    'path': str(static_path)
                }
            else:
                health_status['checks']['static_files'] = {
                    'status': 'warning',
                    'message': 'Static files directory does not exist',
                    'path': str(static_path)
                }
        else:
            health_status['checks']['static_files'] = {
                'status': 'warning',
                'message': 'STATIC_ROOT not configured'
            }
    except Exception as e:
        health_status['checks']['static_files'] = {
            'status': 'warning',
            'message': f'Static files check failed: {str(e)}'
        }
    
    # Settings check
    try:
        debug_mode = getattr(settings, 'DEBUG', None)
        health_status['checks']['settings'] = {
            'status': 'healthy',
            'debug': debug_mode,
            'allowed_hosts_configured': bool(getattr(settings, 'ALLOWED_HOSTS', None))
        }
    except Exception as e:
        health_status['checks']['settings'] = {
            'status': 'warning',
            'message': f'Settings check failed: {str(e)}'
        }
    
    # Update overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
    
    http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JsonResponse(health_status, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_readiness(request):
    """
    Readiness probe endpoint for Kubernetes/Docker.
    
    Checks if the service is ready to accept traffic.
    More comprehensive than basic health check.
    
    GET /health/readiness/
    """
    checks = {}
    ready = True
    
    # Database readiness
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = 'ready'
    except Exception as e:
        ready = False
        checks['database'] = f'not_ready: {str(e)}'
    
    response_data = {
        'ready': ready,
        'checks': checks
    }
    
    http_status = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JsonResponse(response_data, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_liveness(request):
    """
    Liveness probe endpoint for Kubernetes/Docker.
    
    Simple check to determine if the service is alive.
    Should be lightweight and fast.
    
    GET /health/liveness/
    """
    return JsonResponse({
        'alive': True,
        'service': 'playportal-backend'
    }, status=status.HTTP_200_OK)



