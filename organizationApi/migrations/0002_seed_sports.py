# Generated data migration to seed initial sports

from django.db import migrations


def seed_sports(apps, schema_editor):
    """
    Seed initial sports into the database.
    Creates common sports with their appropriate scoring types.
    """
    Sport = apps.get_model('organizationApi', 'Sport')

    # Define sports with their scoring types
    sports_data = [
        {'name': 'Tennis', 'scoring_type': 'sets'},
        {'name': 'Badminton', 'scoring_type': 'sets'},
        {'name': 'Basketball', 'scoring_type': 'simple'},
        {'name': 'Football', 'scoring_type': 'simple'},
        {'name': 'Volleyball', 'scoring_type': 'sets'},
    ]

    # Create sports if they don't already exist (idempotent)
    for sport_data in sports_data:
        Sport.objects.get_or_create(
            name=sport_data['name'],
            defaults={'scoring_type': sport_data['scoring_type']}
        )


def reverse_seed_sports(apps, schema_editor):
    """
    Remove seeded sports when rolling back this migration.
    Only removes the sports we added, not manually created ones.
    """
    Sport = apps.get_model('organizationApi', 'Sport')

    sport_names = ['Tennis', 'Badminton', 'Basketball', 'Football', 'Volleyball']
    Sport.objects.filter(name__in=sport_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('organizationApi', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_sports, reverse_seed_sports),
    ]

