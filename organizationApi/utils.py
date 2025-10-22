import math
import logging
from . models import Team, Match, SetScore, SimpleScore
from django.db import transaction
from django.db import models

logger = logging.getLogger(__name__)


class KoGenContentSwap:
    """
    Context manager to temporarily swap fixture content_object for RR_KO KoGen operations.
    
    This is needed because KoGen expects content_object to be a Knockout instance,
    but RR_KO fixtures have RoundRobinKnockout as content_object.
    
    Usage:
        with KoGenContentSwap(fixture, knockout_phase):
            ko_gen = KoGen(category, data, sets, points)
            result = ko_gen.create_complete_bracket_with_teams()
    """
    def __init__(self, fixture, knockout_phase):
        self.fixture = fixture
        self.knockout_phase = knockout_phase
        self.original = None
    
    def __enter__(self):
        self.original = self.fixture.content_object
        self.fixture.content_object = self.knockout_phase
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fixture.content_object = self.original
        return False

class KoGen:
    def __init__(self, category_instance, json_data=None, no_sets=3, points_to_win=15):
        """Initialize the Knockout Generator."""
        self.json_data = json_data or {"matches": []}
        self.category = category_instance
        self.sport = category_instance.tournament.sport
        
        # Calculate knockout stage based on number of matches
        if "matches" in json_data:
            self.ko_stage = math.ceil(math.log2(len(json_data["matches"])*2))
        else:
            self.ko_stage = 1  # Default if no matches
            
        self.errors = []
        self.no_sets = no_sets
        self.points_to_win = points_to_win
        self.ko_instance = category_instance.fixture.content_object
        
        # Update category settings
        category_instance.required_points = points_to_win
        category_instance.max_sets = no_sets
        category_instance.save()

    def validate(self):
        """Validate the match pairings."""
        if not self.json_data or "matches" not in self.json_data:
            self.errors.append('No match data provided')
            return False
            
        # Store team IDs to ensure no team plays twice
        used_team_ids = set()
        
        for match in self.json_data["matches"]:
            team_1 = match.get('team_1')
            team_2 = match.get('team_2')
            
            # Rule 1: Both teams can't be BYE
            if team_1 == 'BYE' and team_2 == 'BYE':
                self.errors.append('Both teams cannot be BYE in the same match')
            
            # Rule 2: Check if teams exist in this category (if not BYE)
            if team_1 != 'BYE':
                try:
                    team = Team.objects.get(id=team_1, category=self.category)
                    # Rule 3: No team can participate twice
                    if team_1 in used_team_ids:
                        self.errors.append(f'Team {team.name} appears in multiple matches')
                    used_team_ids.add(team_1)
                except Team.DoesNotExist:
                    self.errors.append(f'Team ID {team_1} not found in this category')
                    
            if team_2 != 'BYE':
                try:
                    team = Team.objects.get(id=team_2, category=self.category)
                    if team_2 in used_team_ids:
                        self.errors.append(f'Team {team.name} appears in multiple matches')
                    used_team_ids.add(team_2)
                except Team.DoesNotExist:
                    self.errors.append(f'Team ID {team_2} not found in this category')
                    
        return not bool(self.errors)

    def get_teams(self, match):
        """Get team objects from match data."""
        team_1_id = match.get('team_1')
        team_2_id = match.get('team_2')

        team_1 = Team.objects.get(id=team_1_id) if team_1_id != 'BYE' else None
        team_2 = Team.objects.get(id=team_2_id) if team_2_id != 'BYE' else None

        return team_1, team_2

    def create_match_instance(self, team_1, team_2, match_number):
        """Create a match instance with the given teams."""
        if team_1 is None or team_2 is None:
            winner = team_1 if team_2 is None else team_2
            self.ko_instance.winners_bracket.add(winner)
            return Match.objects.create(
                team1=team_1,
                team2=team_2,
                winner=winner,
                category=self.category,
                sport=self.sport,
                match_number=match_number,
                match_state=True,
                stage_number=self.ko_stage
            )
        else:
            return Match.objects.create(
                team1=team_1,
                team2=team_2,
                category=self.category,
                sport=self.sport,
                match_number=match_number,
                stage_number=self.ko_stage
            )
    
    def create_scores(self, matches, scoring_type):
        """Create score instances for matches based on scoring type."""
        if scoring_type == 'sets':
            # Use bulk_create for better performance with multiple matches
            set_scores = []
            for match in matches:
                for set_num in range(self.no_sets):
                    set_scores.append(SetScore(match=match, set_number=set_num + 1))
            SetScore.objects.bulk_create(set_scores)
        else:
            simple_scores = [SimpleScore(match=match) for match in matches]
            SimpleScore.objects.bulk_create(simple_scores)

    def create_matches(self, use_complete_bracket=False):
        """Create knockout matches based on the provided pairings.
        
        Args:
            use_complete_bracket (bool): If True, generates complete bracket structure
                                        and assigns teams to first stage only.
                                        If False, uses traditional single-stage creation.
        """
        # Validate match data
        if not self.validate():
            return {'errors': self.errors}

        if use_complete_bracket:
            return self.create_complete_bracket_with_teams()
        else:
            return self.create_traditional_matches()
    
    def create_traditional_matches(self):
        """Traditional single-stage match creation (legacy method)."""
        try:
            with transaction.atomic():
                matches = []
                matches_list = []
                scoring_type = self.sport.scoring_type

                for i, match in enumerate(self.json_data["matches"]):
                    team_1, team_2 = self.get_teams(match)
                    match_instance = self.create_match_instance(team_1, team_2, i)
                    team_1_name = team_1.name if team_1 else "BYE"
                    team_2_name = team_2.name if team_2 else "BYE"
                    matches_list.append((team_1_name, team_2_name))
                    
                    matches.append(match_instance)

                self.create_scores(matches, scoring_type)
                self.update_ko_instance(matches, matches_list=matches_list)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error creating knockout matches: {str(e)}")
            return {'error': str(e)}
    
    def create_complete_bracket_with_teams(self):
        """New method: Generate complete bracket and assign teams to first stage."""
        try:
            # Calculate number of teams from provided matches
            num_teams = len(self.json_data["matches"]) * 2
            logger.debug(f"Creating complete bracket for {num_teams} teams")
            
            # Generate complete bracket structure
            self.generate_complete_bracket(num_teams)
            
            # Assign teams to first stage matches
            result = self.assign_teams_to_first_stage(self.json_data["matches"])
            
            if isinstance(result, dict) and ('error' in result or 'errors' in result):
                return result
                
            logger.debug(f"Successfully created complete bracket with team assignments")
            return result
            
        except Exception as e:
            logger.error(f"Error creating complete bracket with teams: {str(e)}")
            return {'error': str(e)}

    def update_ko_instance(self, matches, matches_list=None):
        """Update knockout instance with created matches."""
        self.ko_instance.all_matches.add(*matches)
        self.ko_instance.bracket_matches.add(*[match for match in matches if not match.match_state])
        
        # if matches_list:
            # self.ko_instance.json = KnockoutManager(initial_matches=matches_list).to_json()
        self.ko_instance.save()

    def calculate_bracket_structure(self, num_teams):
        """Calculate complete bracket structure details."""
        total_stages = math.ceil(math.log2(num_teams))
        bracket_structure = {}
        
        for stage in range(total_stages, 0, -1):
            matches_in_stage = 2 ** (stage - 1)
            bracket_structure[stage] = {
                'matches_count': matches_in_stage,
                'stage_name': self.get_stage_name(stage, total_stages)
            }
            
        return total_stages, bracket_structure
    
    def get_stage_name(self, stage, total_stages):
        """Get human-readable stage name."""
        if stage == 1:
            return "Final"
        elif stage == 2:
            return "Semi-Final"
        elif stage == 3:
            return "Quarter-Final"
        else:
            return f"Round {total_stages - stage + 1}"
    
    def generate_complete_bracket(self, num_teams):
        """Generate complete knockout bracket structure without teams."""
        total_stages, bracket_structure = self.calculate_bracket_structure(num_teams)
        
        logger.debug(f"Generating complete bracket for {num_teams} teams with {total_stages} stages")
        
        try:
            with transaction.atomic():
                all_matches = []
                
                # Create matches stage by stage from highest to lowest
                for stage in range(total_stages, 0, -1):
                    matches_in_stage = bracket_structure[stage]['matches_count']
                    stage_name = bracket_structure[stage]['stage_name']
                    
                    logger.debug(f"Creating {matches_in_stage} matches for {stage_name} (stage {stage})")
                    
                    for match_num in range(matches_in_stage):
                        # Create empty match - teams will be assigned later
                        match = Match.objects.create(
                            category=self.category,
                            sport=self.sport,
                            match_number=match_num,
                            stage_number=stage,
                            team1=None,  # Will be assigned when teams are available
                            team2=None   # Will be assigned when teams are available
                        )
                        all_matches.append(match)
                        
                        # Create score instances for empty matches
                        self.create_scores([match], self.sport.scoring_type)
                
                # Update KO instance with all matches
                self.ko_instance.all_matches.add(*all_matches)
                # Only matches with teams go to bracket_matches initially
                self.ko_instance.save()
                
                logger.debug(f"Successfully created complete bracket with {len(all_matches)} matches")
                return all_matches
                
        except Exception as e:
            logger.error(f"Error generating complete bracket: {str(e)}")
            raise
    
    def assign_teams_to_first_stage(self, matches_data):
        """Assign teams to first stage matches in pre-generated bracket."""
        if not self.validate():
            return {'errors': self.errors}
            
        try:
            with transaction.atomic():
                # Get first stage matches (highest stage number)
                first_stage_number = self.ko_instance.all_matches.aggregate(
                    max_stage=models.Max('stage_number')
                )['max_stage']
                
                first_stage_matches = self.ko_instance.all_matches.filter(
                    stage_number=first_stage_number
                ).order_by('match_number')
                
                if len(matches_data) != first_stage_matches.count():
                    return {'error': f'Expected {first_stage_matches.count()} matches, got {len(matches_data)}'}
                
                updated_matches = []
                for i, match_data in enumerate(matches_data):
                    match = first_stage_matches[i]
                    team_1, team_2 = self.get_teams(match_data)
                    
                    # Assign teams to existing match
                    match.team1 = team_1
                    match.team2 = team_2
                    
                    # Handle BYE scenarios
                    if team_1 is None or team_2 is None:
                        winner = team_1 if team_2 is None else team_2
                        match.winner = winner
                        match.match_state = True
                        self.ko_instance.winners_bracket.add(winner)
                        # Immediately progress winner to next match
                        self.progress_winner_to_next_match(match)
                    else:
                        # Match is ready to be scheduled
                        self.ko_instance.bracket_matches.add(match)
                    
                    match.save()
                    updated_matches.append(match)
                
                self.ko_instance.save()
                return updated_matches
                
        except Exception as e:
            logger.error(f"Error assigning teams to first stage: {str(e)}")
            return {'error': str(e)}
    
    def progress_winner_to_next_match(self, completed_match):
        """Progress winner to next match immediately using mathematical progression."""
        if completed_match.stage_number <= 1:  # Final match
            self.category.winner = completed_match.winner
            self.category.save()
            logger.info(f"Tournament completed! Winner: {completed_match.winner.name}")
            return
            
        # Calculate next match using mathematical relationships
        next_match_number = completed_match.match_number // 2
        next_stage = completed_match.stage_number - 1
        parent_slot = completed_match.match_number % 2  # 0 or 1
        
        logger.debug(f"Progressing winner from Stage {completed_match.stage_number} Match {completed_match.match_number} to Stage {next_stage} Match {next_match_number} Slot {parent_slot}")
        
        try:
            next_match = Match.objects.get(
                category=self.category,
                stage_number=next_stage,
                match_number=next_match_number
            )
            
            # Assign winner to correct slot
            if parent_slot == 0:
                next_match.team1 = completed_match.winner
                logger.debug(f"Assigned {completed_match.winner.name} to team1 slot")
            else:
                next_match.team2 = completed_match.winner
                logger.debug(f"Assigned {completed_match.winner.name} to team2 slot")
                
            next_match.save()
            
            # Check if next match can be scheduled (both teams ready)
            if next_match.team1 and next_match.team2:
                self.ko_instance.bracket_matches.add(next_match)
                logger.debug(f"Next match ready for scheduling: {next_match.team1.name} vs {next_match.team2.name}")
                
        except Match.DoesNotExist:
            logger.error(f"Next match not found: Stage {next_stage}, Match {next_match_number}")
            # This shouldn't happen with pre-generated brackets
            raise

class ScoreManager:
    """Manager for handling match score updates in both simple and set-based scoring systems."""
    
    def __init__(self, request, match_instance, category_instance):
        """Initialize with match and request data."""
        self.data = request.data
        self.match = match_instance
        self.category = category_instance
        self.team_id = None if self.data.get('action') == 'finish' else int(self.data.get('team_id', 0))
        self.fixture = category_instance.fixture
        self.sport = match_instance.sport
        self.court_advancement = None  # NEW: Store court advancement information
        
    def validate(self):
        """Validate match and request data."""
        if self.match.match_state:
            return {'error': 'Match already completed!', 'success': False}
            
        if not self.match.team1 or not self.match.team2:
            return {'error': 'Match teams not set', 'success': False}
            
        if self.data.get('action') != 'finish':
            if not self.team_id or self.team_id not in [self.match.team1.id, self.match.team2.id]:
                return {'error': 'Invalid team ID', 'success': False}
        
        if not self.fixture.scheduled_matches.filter(id=self.match.id).exists():
            return {'error': 'Match not scheduled!', 'success': False}
            
        if self.sport.scoring_type == 'sets':
            current_set = self.get_current_set()
            if not current_set:
                return {'error': 'All sets completed!', 'success': False}
        else:
            if not hasattr(self.match, 'score_system'):
                return {'error': 'Score system not initialized', 'success': False}
                
        return None
    
    def process_score_update(self, action):
        """Process score update based on action type."""
        validation_result = self.validate()
        if validation_result:
            return validation_result
            
        if self.sport.scoring_type == 'sets':
            if action == 'finish':
                return {'error': 'Finish action not valid for sets scoring', 'success': False}
            return self.update_set_score(action == 'increment')
        else:
            return self.update_simple_score(action)
    
    def get_current_set(self):
        """Get current active set."""
        return self.match.sets.filter(set_state=False).order_by('set_number').first()
    
    @transaction.atomic
    def update_set_score(self, is_increment):
        """Update score for set-based matches."""
        current_set = self.get_current_set()
        
        # Update points based on action
        if is_increment:
            if self.team_id == self.match.team1.id:
                current_set.team1_points += 1
            else:
                current_set.team2_points += 1
        else:
            if self.team_id == self.match.team1.id:
                current_set.team1_points = max(0, current_set.team1_points - 1)
            else:
                current_set.team2_points = max(0, current_set.team2_points - 1)
                
        current_set.save()
        
        # Check set completion
        if self.check_set_completion(current_set):
            response = {
                'success': True, 
                'message': 'Set completed, proceeding to next set or match completion'
            }
            # Add court advancement information if match was completed
            self._add_court_advancement_to_response(response)
            return response
            
        return {
            'success': True, 
            'message': f'Set score {"incremented" if is_increment else "decremented"} successfully'
        }
    
    @transaction.atomic
    def update_simple_score(self, action):
        """Update score for simple scoring matches."""
        simple_score = self.match.score_system
        
        if action == 'increment':
            if self.team_id == self.match.team1.id:
                simple_score.team1_score += 1
            else:
                simple_score.team2_score += 1
            simple_score.save()
            return {'success': True, 'message': 'Score incremented successfully'}
            
        elif action == 'decrement':
            if self.team_id == self.match.team1.id:
                simple_score.team1_score = max(0, simple_score.team1_score - 1)
            else:
                simple_score.team2_score = max(0, simple_score.team2_score - 1)
            simple_score.save()
            return {'success': True, 'message': 'Score decremented successfully'}
            
        elif action == 'finish':
            return self.finish_match(simple_score)
    
    def check_set_completion(self, current_set):
        """Check if current set is complete and handle match completion if needed."""
        required_points = self.category.required_points
        
        if current_set.team1_points >= required_points or current_set.team2_points >= required_points:
            current_set.set_state = True
            current_set.winner = (self.match.team1 
                                if current_set.team1_points > current_set.team2_points 
                                else self.match.team2)
            current_set.save()
            
            return self.check_match_completion()
            
        return False
    
    def check_match_completion(self):
        """Check if match is complete based on set wins."""
        team1_wins = self.match.sets.filter(winner=self.match.team1).count()
        team2_wins = self.match.sets.filter(winner=self.match.team2).count()
        majority = (self.category.max_sets // 2) + 1
        
        if team1_wins >= majority or team2_wins >= majority:
            self.match.winner = (self.match.team1 if team1_wins > team2_wins 
                               else self.match.team2)
            self.match.match_state = True
            self.match.save()
            self.handle_match_completion()
            return True
            
        return False
    
    def _add_court_advancement_to_response(self, response):
        """Add court advancement information to response if available."""
        if self.court_advancement:
            advancement = self.court_advancement['advancement_result']
            response['court_advancement'] = {
                'court_id': self.court_advancement['court_id'],
                'court_name': self.court_advancement['court_name'],
                'advanced': advancement.get('advanced', False),
                'previous_match_id': advancement.get('previous_match_id'),
                'new_current_match': advancement.get('new_current_match'),
                'court_available': advancement.get('court_available', False),
                'remaining_queue_count': advancement.get('remaining_queue_count', 0)
            }
            
            # Enhance message with court information
            if advancement.get('new_current_match'):
                next_match = advancement['new_current_match']
                response['message'] += f" Court {self.court_advancement['court_name']} advanced to next match: {next_match['team1']} vs {next_match['team2']}"
            elif advancement.get('court_available'):
                response['message'] += f" Court {self.court_advancement['court_name']} is now available"
    
    def finish_match(self, simple_score):
        """Complete a simple scoring match."""
        if self.match.match_state:
            return {'error': 'Match already completed!', 'success': False}
            
        if simple_score.team1_score == simple_score.team2_score:
            return {'error': 'Scores are tied, cannot determine winner', 'success': False}
            
        self.match.winner = (self.match.team1 
                           if simple_score.team1_score > simple_score.team2_score 
                           else self.match.team2)
        self.match.match_state = True
        self.match.save()
        self.handle_match_completion()
        
        # Enhanced response with court advancement information
        response = {'success': True, 'message': 'Match completed successfully'}
        self._add_court_advancement_to_response(response)
        return response
    
    def handle_match_completion(self):
        """Handle post-match completion tasks including court advancement."""
        self.fixture.scheduled_matches.remove(self.match)
        
        # NEW: Auto-advance court if this match was assigned to a court
        self.advance_court_if_assigned()
        
        if self.fixture.fixtureType == 'KO':
            self.handle_ko_completion()
        elif self.fixture.fixtureType == 'RR':
            self.handle_rr_completion()
        elif self.fixture.fixtureType == 'RR_KO':
            # For RR_KO, check if this match belongs to KO phase
            rr_ko_instance = self.fixture.content_object
            
            # Check if match belongs to knockout phase (not just current_phase status)
            if rr_ko_instance.knockout_phase and \
               rr_ko_instance.knockout_phase.all_matches.filter(id=self.match.id).exists():
                # This is a KO match - handle progression
                self.handle_ko_completion_for_rr_ko(rr_ko_instance)
            # If it's an RR match, no special handling needed (already removed from scheduled_matches)
    
    def advance_court_if_assigned(self):
        """Automatically advance court to next match if this match was current."""
        try:
            # Check if this match was assigned to a court as the current match
            from .models import Court
            court = Court.objects.filter(current_match=self.match).first()
            
            if court:
                logger.info(f"Match {self.match.id} completed on {court.name}, advancing to next match")
                advancement_result = court.advance_to_next_match()
                
                # Store advancement info for response enhancement
                self.court_advancement = {
                    'court_id': court.id,
                    'court_name': court.name,
                    'advancement_result': advancement_result
                }
                
                # Log the advancement details
                if advancement_result.get('new_current_match'):
                    next_match = advancement_result['new_current_match']
                    logger.info(f"Court {court.name} advanced to match {next_match['id']}: "
                              f"{next_match['team1']} vs {next_match['team2']}")
                elif advancement_result.get('court_available'):
                    logger.info(f"Court {court.name} is now available (no more queued matches)")
                    
        except Exception as e:
            # Don't fail match completion if court advancement fails
            logger.error(f"Error advancing court after match completion: {str(e)}")
            self.court_advancement = None
            # Continue with normal match completion flow
    
    def handle_ko_completion(self):
        """Handle knockout tournament progression with immediate advancement."""
        ko_instance = self.fixture.content_object
        ko_instance.winners_bracket.add(self.match.winner)
        ko_instance.save()
        
        # Use new immediate progression logic
        ko_gen = KoGen(self.category, {}, self.category.max_sets, self.category.required_points)
        ko_gen.progress_winner_to_next_match(self.match)
        
        logger.debug(f"Match completed: {self.match.winner.name} progressed to next stage")
    
    def handle_ko_completion_for_rr_ko(self, rr_ko_instance):
        """Handle knockout phase completion for RR_KO tournaments."""
        ko_instance = rr_ko_instance.knockout_phase
        ko_instance.winners_bracket.add(self.match.winner)
        ko_instance.save()
        
        # Use context manager to swap content_object for KoGen
        with KoGenContentSwap(self.fixture, ko_instance):
            ko_gen = KoGen(self.category, {}, self.category.max_sets, self.category.required_points)
            ko_gen.progress_winner_to_next_match(self.match)
        
        logger.debug(f"RR_KO Match completed: {self.match.winner.name} progressed to next stage")
    
    def handle_rr_completion(self):
        """Handle round robin statistics update."""
        rr_instance = self.fixture.content_object
        if hasattr(rr_instance, 'update_team_stats'):
            rr_instance.update_team_stats(self.match)
        rr_instance.save()
    
    # Note: schedule_next_ko_stage method has been removed and replaced with 
    # immediate progression logic in KoGen.progress_winner_to_next_match()
    # This provides better performance and allows matches to be scheduled
    # as soon as both teams are available, rather than waiting for entire stages.

