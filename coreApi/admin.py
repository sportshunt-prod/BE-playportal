from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *


class CustomUserAdmin(BaseUserAdmin):
    """
    Custom User admin that handles both password-based and OAuth users.
    """
    # Fields to display in the user list
    list_display = ('username', 'email', 'is_organizer', 'is_staff', 'is_active')

    # Add is_organizer to the fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Organization', {'fields': ('is_organizer',)}),
    )
    
    # Add is_organizer to add form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Organization', {'fields': ('is_organizer',)}),
    ) 

# Register your models here.
admin.site.register(User, CustomUserAdmin)
admin.site.register(Order)