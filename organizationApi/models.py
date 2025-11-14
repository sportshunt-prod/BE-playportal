from django.db import models
from coreApi.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from datetime import datetime
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import json
import math

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
        return self.name


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
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='tournaments')

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
        return self.teams.count()
    
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
        set_scores = []
        simple_scores = []
        
        for round_no in range(1, self.rounds + 1):
            for i, team1 in enumerate(teams):
                for j, team2 in enumerate(teams):
                    if i < j:
                        match = Match.objects.create(
                            team1=team1.team,
                            team2=team2.team,
                            category=self.category,
                            sport=sport,
                            match_number=self.all_matches.count() + len(matches) + 1,
                            stage_number=round_no,
                        )
                        matches.append(match)
                        
                        # Prepare score objects for bulk creation
                        if sport.scoring_type == 'sets':
                            for set_num in range(self.category.max_sets):
                                set_scores.append(SetScore(
                                    match=match, 
                                    set_number=set_num + 1
                                ))
                        else:
                            simple_scores.append(SimpleScore(match=match))
        
        # Bulk create scores for better performance
        if set_scores:
            SetScore.objects.bulk_create(set_scores)
        if simple_scores:
            SimpleScore.objects.bulk_create(simple_scores)
            
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
        """
        Get teams sorted by performance.
        Primary: matches_won (descending)
        Secondary: matches_lost (ascending - fewer losses is better)
        """
        return self.rr_teams.order_by('-matches_won', 'matches_lost')
    
    def __str__(self):
        return f"Round Robin - {self.category.name} - {self.category.tournament.name}"


class RoundRobinKnockout(models.Model):
    """
    Two-phase tournament: Round Robin → Knockout.
    
    LIFECYCLE: RR phase → all teams play → top 50% qualify → KO phase auto-created → winner
    STATE: round_robin_completed, knockout_started flags; current_phase property
    QUALIFICATION: Sorted by wins/losses, tiebreaker via head-to-head results
    AUTO-CREATION: KO matches created automatically when last RR match completes
    """
    round_robin_phase = models.ForeignKey(RoundRobin, on_delete=models.CASCADE, related_name='rr_ko_tournament', null=True, blank=True)
    knockout_phase = models.ForeignKey(Knockout, on_delete=models.CASCADE, null=True, blank=True, related_name='rr_ko_tournament')
    round_robin_completed = models.BooleanField(default=False)
    knockout_started = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='rr_ko_category', null=True)
    
    def initialize_round_robin(self, rounds=1):
        """
        Create and setup RR phase with all teams, matches, and scores.
        Called by serializer when creating RR_KO fixture.
        """
        if not self.round_robin_phase:
            # Create RoundRobin instance
            round_robin = RoundRobin.objects.create(
                category=self.category,
                rounds=rounds
            )
            
            # Create RR_Team entries for all teams
            teams = self.category.teams.all()
            rr_teams = [RR_Team(team=team, round_robin=round_robin) for team in teams]
            created_rr_teams = RR_Team.objects.bulk_create(rr_teams)
            round_robin.rr_teams.set(created_rr_teams)
            
            # Schedule all round robin matches (creates Match + Score objects)
            round_robin.schedule_matches()
            
            # Link the round robin phase
            self.round_robin_phase = round_robin
            self.save()
            round_robin.save()
            
            return round_robin
        return self.round_robin_phase
    
    def start_knockout(self, qualified_teams):
        """
        Start KO phase with qualified teams.
        Similar to how KO fixture is created - just creates Knockout instance.
        Matches will be created later via create_ko_matches endpoint.
        """
        if self.round_robin_completed and not self.knockout_started:
            # Create Knockout instance (same as regular KO)
            knockout = Knockout.objects.create(category=self.category)
            knockout.bracket_teams.set(qualified_teams)
            
            total_teams = len(qualified_teams) if isinstance(qualified_teams, list) else qualified_teams.count()
            knockout.ko_stage = math.ceil(math.log2(total_teams))
            knockout.save()
            
            # Link the knockout phase
            self.knockout_phase = knockout
            self.knockout_started = True
            self.save()
            
            return knockout
        return None
    
    @property
    def  current_phase(self):
        """Returns 'round_robin' or 'knockout' based on knockout_started flag."""
        if self.knockout_started:
            return 'knockout'
        else:
            return 'round_robin'
    
    def check_round_robin_completion(self):
        """Check if round robin phase is complete and update status"""
        if not self.round_robin_completed:
            total_matches = self.round_robin_phase.all_matches.count()
            if total_matches == 0:
                return False
            
            completed_matches = self.round_robin_phase.all_matches.filter(
                match_state=True
            ).count()
            
            if completed_matches == total_matches:
                self.round_robin_completed = True
                self.save()
                return True
        
        return False
    
    def get_qualified_teams(self, num_teams=8):
        """Get top teams from round robin phase with head-to-head tiebreaker."""
        if not self.round_robin_completed:
            return []
        
        leaderboard = list(self.round_robin_phase.get_leaderboard())
        
        # Simple approach: check adjacent teams for ties
        result = []
        i = 0
        while i < len(leaderboard):
            # Collect all teams with same wins/losses as current team
            current_team = leaderboard[i]
            tied_group = [current_team]
            j = i + 1
            
            while j < len(leaderboard):
                if (leaderboard[j].matches_won == current_team.matches_won and 
                    leaderboard[j].matches_lost == current_team.matches_lost):
                    tied_group.append(leaderboard[j])
                    j += 1
                else:
                    break
            
            # If multiple teams tied, resolve head-to-head
            if len(tied_group) > 1:
                resolved = self._resolve_head_to_head(tied_group)
                result.extend(resolved)
            else:
                result.append(current_team)
            
            i = j  # Move to next group
        
        return [entry.team for entry in result[:num_teams]]
    
    def _resolve_head_to_head(self, tied_teams):
        """
        Resolve ties using head-to-head match results.
        For 2 teams: Check who won their match
        For 3+ teams: Count wins among tied teams only
        """
        if len(tied_teams) <= 1:
            return tied_teams
        
        # Handle 2-team tie: simple head-to-head winner lookup
        if len(tied_teams) == 2:
            team1 = tied_teams[0].team
            team2 = tied_teams[1].team
            
            # Use Q() for bidirectional lookup (team1 vs team2 OR team2 vs team1)
            match = self.round_robin_phase.all_matches.filter(
                models.Q(team1=team1, team2=team2) | 
                models.Q(team1=team2, team2=team1),
                match_state=True
            ).first()
            
            # Return winner first, loser second
            if match and match.winner:
                if match.winner == team1:
                    return [tied_teams[0], tied_teams[1]]
                else:
                    return [tied_teams[1], tied_teams[0]]
            # No winner or match not found: maintain original order
            return tied_teams
        
        # Handle 3+ team tie: mini round-robin among tied teams only
        else:
            team_ids = [t.team.id for t in tied_teams]
            
            # Find all matches between ONLY the tied teams
            h2h_matches = self.round_robin_phase.all_matches.filter(
                team1__id__in=team_ids,
                team2__id__in=team_ids,
                match_state=True
            )
            
            # Count wins among tied teams only (ignores wins against non-tied teams)
            h2h_wins = {}
            for team_entry in tied_teams:
                wins = h2h_matches.filter(winner=team_entry.team).count()
                h2h_wins[team_entry] = wins
            
            # Sort by head-to-head wins (desc)
            return sorted(tied_teams, key=lambda t: h2h_wins.get(t, 0), reverse=True)
    
    def __str__(self):
        phase = self.current_phase.capitalize()
        return f"Round Robin + Knockout ({phase}) - {self.category.name} - {self.category.tournament.name}"


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
        """
        Returns the number of sets won by team1.
        Note: This property performs a database query each time it's accessed.
        Consider caching or denormalization if used frequently in templates or API responses.
        """
        if self.sport.scoring_type == 'sets':
            return self.sets.filter(winner=self.team1).count()
        return 0

    @property
    def team2_sets_won(self):
        """
        Returns the number of sets won by team2.
        Note: This property performs a database query each time it's accessed.
        Consider caching or denormalization if used frequently in templates or API responses.
        """
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
        team1_name = self.match.team1.name if self.match.team1 else "TBD"
        team2_name = self.match.team2.name if self.match.team2 else "TBD"
        return f"{team1_name} ({self.team1_score}) vs {team2_name} ({self.team2_score})"


# Court Model
class Court(models.Model):
    name = models.CharField(max_length=255)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='courts')
    current_match = models.ForeignKey('Match', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_court')
    upcoming_matches = models.ManyToManyField('Match', related_name='upcoming_courts', blank=True)

    def advance_to_next_match(self):
        """
        Advance court to next match in queue.
        
        Returns:
            dict: Information about the advancement
        """
        next_matches = self.upcoming_matches.order_by('id')
        
        if next_matches.exists():
            next_match = next_matches.first()
            previous_match = self.current_match
            
            # Advance to next match
            self.current_match = next_match
            self.upcoming_matches.remove(next_match)
            self.save()
            
            return {
                'advanced': True,
                'previous_match_id': previous_match.id if previous_match else None,
                'new_current_match': {
                    'id': next_match.id,
                    'team1': next_match.team1.name if next_match.team1 else 'BYE',
                    'team2': next_match.team2.name if next_match.team2 else 'BYE',
                    'category': next_match.category.name
                },
                'remaining_queue_count': self.upcoming_matches.count()
            }
        else:
            # No more matches in queue - court becomes available
            previous_match = self.current_match
            self.current_match = None
            self.save()
            
            return {
                'advanced': True,
                'previous_match_id': previous_match.id if previous_match else None,
                'new_current_match': None,
                'remaining_queue_count': 0,
                'court_available': True
            }
            
    def __str__(self):
        return f"{self.name} - {self.tournament.name}"