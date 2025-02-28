from django.db import models
from coreApi.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from datetime import datetime
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import json

phone_regex = RegexValidator(
    regex=r'^\d{10}$',
    message="Phone number must be 10 digits"
)

def validate_dates(start_date, end_date):
    if end_date < start_date:
        raise ValidationError("End date must be after start date")

# Sport and Scoring System Models
class Sport(models.Model):

    SCORING_TYPES = [
        ('sets', 'Set-based scoring'),
        ('simple', 'Simple score'),
    ]
    
    name = models.CharField(max_length=20, unique=True)
    scoring_type = models.CharField(max_length=10, choices=SCORING_TYPES)

    def __str__(self):
        return self.get_name_display()


# Organization and Tournament Models
class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    ph_number = models.CharField(max_length=10, validators=[phone_regex])
    mail = models.EmailField(max_length=255)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organization")

    def __str__(self):
        return self.name


class Tournament(models.Model):
    name = models.CharField(max_length=255)
    details = models.TextField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="tournaments")
    start_date = models.DateField()
    end_date = models.DateField()
    venue_address = models.CharField(max_length=1024)
    venue_link = models.URLField(max_length=512, blank=True, null=True)
    ph_number = models.CharField(max_length=10, default="", validators=[phone_regex])
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='tournaments', default=1)

    class Meta:
        ordering = ['start_date']

    def clean(self):
        if self.start_date and self.end_date:
            validate_dates(self.start_date, self.end_date)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def completed(self):
        return self.end_date < datetime.now().date()
    
    @property
    def start_month(self):
        return self.start_date.strftime('%b').upper()
    
    @property
    def start_day_date(self):
        return self.start_date.strftime('%d')
    
    @property
    def card_details(self):
        return f"by {self.organization.name} on {self.start_date.strftime('%d %b')}"
    
    @property
    def end_date_(self):
        return self.end_date.strftime('%d %b')
    
    def __str__(self):
        return f"{self.name} - {self.organization.name}"


# Category and Fixture Models
class Category(models.Model):
    name = models.CharField(max_length=255)
    details = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    winner = models.ForeignKey('Team', on_delete=models.SET_NULL, blank=True, null=True, related_name="won_categories")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="categories")
    fixture = models.ForeignKey('Fixture', on_delete=models.SET_NULL, related_name="category_fixture", blank=True, null=True)
    registration_status = models.BooleanField(default=True)
    max_sets = models.PositiveSmallIntegerField(default=3, blank=True)  # Badminton-specific
    required_points = models.PositiveSmallIntegerField(default=21, blank=True)  # Badminton-specific

    @property
    def entries_cnt(self):
        return self.teams.all().count()
    
    @property
    def reg_status(self):
        return "Open" if self.registration_status else "Closed"
    
    def __str__(self):
        return f"{self.name} - {self.tournament.name}"


class Fixture(models.Model):
    FIXTURE_CHOICES = [
        ('KO', 'Knockout'),
        ('RR', 'Round Robin'),
        ('RR_KO', 'Round Robin + Knockout'),
    ]
    fixtureType = models.CharField(max_length=5, choices=FIXTURE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="fixture_category", blank=True, null=True)
    fixture_data = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('fixture_data', 'object_id')
    scheduled_matches = models.ManyToManyField('Match', related_name='scheduled_matches', blank=True)
    
    def save(self, *args, **kwargs):
        if self.fixtureType == 'KO':
            self.fixture_data = ContentType.objects.get_for_model(Knockout)
        elif self.fixtureType == 'RR':
            self.fixture_data = ContentType.objects.get_for_model(RoundRobin)
        elif self.fixtureType == 'RR_KO':
            self.fixture_data = ContentType.objects.get_for_model(RoundRobinKnockout)
        super(Fixture, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        matches = self.scheduled_matches.all()
        for match in matches:
            match.delete()
        super(Fixture, self).delete(*args, **kwargs)
    
    def __str__(self):
        return f"Fixture - {self.fixtureType} - {self.category.name} - {self.category.tournament.name}"


# Fixture Types
class Knockout(models.Model):
    _json = models.TextField(db_column='json', blank=True, null=True)
    fixing_manual = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="category")
    bracket_teams = models.ManyToManyField('Team', related_name='bracket', blank=True)
    winners_bracket = models.ManyToManyField('Team', related_name='bracket_winners', blank=True)
    bracket_matches = models.ManyToManyField('Match', related_name='bracket_match', blank=True)
    all_matches = models.ManyToManyField('Match', related_name='bracket_all_matches', blank=True)
    ko_stage = models.IntegerField(default=-1)
    
    def delete(self, *args, **kwargs):
        matches = self.all_matches.all()
        for match in matches:
            match.delete()
        super(Knockout, self).delete(*args, **kwargs)
        
    @property
    def json(self):
        return json.loads(self._json) if self._json else None
        
    @json.setter
    def json(self, value):
        self._json = json.dumps(value) if value is not None else None
    
    def __str__(self):
        return f"Knockout - {self.category.name} - {self.category.tournament.name}"


class RR_Team(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='rr_team')
    round_robin = models.ForeignKey('RoundRobin', on_delete=models.CASCADE, related_name='rr_teams')
    run_rate = models.IntegerField(default=0)
    matches_played = models.IntegerField(default=0)
    matches_won = models.IntegerField(default=0)
    matches_lost = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.team.name} - Points: {self.matches_won}"


class RoundRobin(models.Model):
    rounds = models.IntegerField(default=1)
    bracket_matches = models.ManyToManyField('Match', related_name='rr_match', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="rr_category")
    all_matches = models.ManyToManyField('Match', related_name='rr_all_matches', blank=True)
     
    def schedule_matches(self):
        sport = self.category.tournament.sport
        teams = self.rr_teams.all()
        matches = []
        for round_no in range(1, self.rounds + 1):
            for i, team1 in enumerate(teams):
                for j, team2 in enumerate(teams):
                    if i < j:
                        match = Match.objects.create(
                            team1=team1.team,
                            team2=team2.team,
                            category=self.category,
                            sport=sport,
                            match_number=len(self.all_matches.all()) + 1,
                            stage_number=round_no,
                        )
                        if sport.scoring_type == 'sets':
                            for set_num in range(self.category.max_sets):
                                SetScore.objects.create(match=match, set_number=set_num+1)
                        else:
                            SimpleScore.objects.create(match=match)
                        matches.append(match)
        self.bracket_matches.set(matches)
        self.all_matches.add(*matches)
        
        self.save()
        
    def update_team_stats(self, match):
        """
        Update RoundRobinTeam stats after a match is completed.
        """
        if match.winner:
            rr_teams = self.rr_teams.all()
            loser_team = match.team1 if match.winner != match.team1 else match.team2
            for team in rr_teams:
                if team.team == match.winner:
                    winner_team = team
                if team.team == loser_team:
                    loser_team = team
                
            winner_team.matches_won += 1
            loser_team.matches_lost += 1
            
            winner_team.save()
            loser_team.save()
        
        for team in [match.team1, match.team2]:
            rr_team = self.rr_teams.get(team=team)
            rr_team.matches_played += 1
            rr_team.save()
            
    def get_leaderboard(self):
        return self.rr_teams.order_by('-matches_won')
    
    def __str__(self):
        return f"Round Robin - {self.category.name} - {self.category.tournament.name}"


class RoundRobinKnockout(models.Model):
    # [Add fields as needed]
    def __str__(self):
        return f"Round Robin + Knockout - {self.category.name} - {self.category.tournament.name}"


# Team and Match Models
class Team(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="teams")

    def __str__(self):
        return f"{self.name} - {self.category.name} - {self.category.tournament.name}"


class Match(models.Model):
    team1 = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name="match_team1", blank=True, null=True)
    team2 = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name="match_team2", blank=True, null=True)
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name="match_winner", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="match_category")
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='matches')
    match_state = models.BooleanField(default=False)
    match_number = models.IntegerField(null=True, blank=True)
    stage_number = models.IntegerField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    score_system = GenericForeignKey('content_type', 'object_id')

    @property
    def team1_sets_won(self):
        if self.sport.scoring_type == 'sets':
            return self.sets.filter(winner=self.team1).count()
        return 0

    @property
    def team2_sets_won(self):
        if self.sport.scoring_type == 'sets':
            return self.sets.filter(winner=self.team2).count()
        return 0

    def save(self, *args, **kwargs):
        if self.sport.scoring_type == 'sets':
            self.content_type = ContentType.objects.get_for_model(SetScore)
        else:
            self.content_type = ContentType.objects.get_for_model(SimpleScore)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.sport.scoring_type == 'sets':
            scores = self.sets.all()
            for score in scores:
                score.delete()
        else:
            score = self.score_system
            score.delete()
        super(Match, self).delete(*args, **kwargs)
        
    def __str__(self):
        team1, team2 = "Bye", "Bye"
        if self.team1:
            team1 = self.team1.name
        if self.team2:
            team2 = self.team2.name
        return f"{team1} vs {team2} - {self.category.name} - {self.category.tournament.name}"

    @property
    def current_set(self):
        if self.sport.scoring_type == 'sets':
            return self.sets.order_by('set_number').filter(set_state=False).first()
        return None


# Scoring Models
class SetScore(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='sets')
    set_number = models.PositiveSmallIntegerField()
    team1_points = models.PositiveSmallIntegerField(default=0)
    team2_points = models.PositiveSmallIntegerField(default=0)
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name='set_winner', blank=True, null=True)
    set_state = models.BooleanField(default=False)

    class Meta:
        unique_together = ('match', 'set_number')

        # def __str__(self):
        #     return f"Set {self.set_number} - {self.match.team1.name} vs {self.match.team2.name}"


class SimpleScore(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, primary_key=True, related_name='score_system')
    team1_score = models.PositiveSmallIntegerField(default=0)
    team2_score = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.match.team1.name} ({self.team1_score}) vs {self.match.team2.name} ({self.team2_score})"


# Court Model
class Court(models.Model):
    name = models.CharField(max_length=255)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='courts')
    current_match = models.ForeignKey('Match', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_court')
    upcoming_matches = models.ManyToManyField('Match', related_name='upcoming_courts', blank=True)

    def advance_to_next_match(self):
        next_matches = self.upcoming_matches.order_by('id')
        if next_matches.exists():
            next_match = next_matches.first()
            self.current_match = next_match
            self.upcoming_matches.remove(next_match)
        else:
            self.current_match = None
        self.save()
            
    def __str__(self):
        return f"{self.name} - {self.tournament.name}"