from django.contrib import admin
from .models import *

admin.site.register(Organization)
admin.site.register(Tournament)
admin.site.register(Sport)
admin.site.register(Category)
admin.site.register(Fixture)
admin.site.register(Knockout)
admin.site.register(RR_Team)
admin.site.register(RoundRobin)
admin.site.register(RoundRobinKnockout)
admin.site.register(Team)
admin.site.register(Match)
admin.site.register(SetScore)
admin.site.register(SimpleScore)
admin.site.register(Court)