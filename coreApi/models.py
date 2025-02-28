from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_organizer = models.BooleanField('organizer status', default=False)
    
    def __str__(self):
        return (
            f"{self.username}"
        )


class Order(models.Model):
    order_id = models.CharField(max_length=100, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    order_timestamp = models.DateTimeField(auto_now_add=True)
    signature = models.CharField(max_length=255, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    team_instance = models.ForeignKey("organizationApi.Team", on_delete=models.CASCADE, blank=True, null=True)
    team_name = models.CharField(max_length=100)
    category_instance = models.ForeignKey("organizationApi.Category", on_delete=models.CASCADE, blank=True, null=True)
    tournament_instance = models.ForeignKey("organizationApi.Tournament", on_delete=models.CASCADE, blank=True, null=True)
    