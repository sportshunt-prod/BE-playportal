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
        for match in matches:
            if scoring_type == 'sets':
                for set_num in range(self.no_sets):
                    SetScore.objects.create(match=match, set_number=set_num + 1)
            else:
                SimpleScore.objects.create(match=match)

    def create_matches(self):
        """Create knockout matches based on the provided pairings."""
        # Validate match data
        if not self.validate():
            return {'errors': self.errors}

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

    def update_ko_instance(self, matches, matches_list=None):
        """Update knockout instance with created matches."""
        self.ko_instance.all_matches.add(*matches)
        self.ko_instance.bracket_matches.add(*[match for match in matches if not match.match_state])
        
        # if matches_list:
            # self.ko_instance.json = KnockoutManager(initial_matches=matches_list).to_json()
        self.ko_instance.save()

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
    
    def validate(self):
        """Validate match and request data."""
        if self.match.match_state:
            return {'error': 'Match already completed!', 'success': False}
            
        if not self.match.team1 or not self.match.team2:
            return {'error': 'Match teams not set', 'success': False}
            
        if self.data.get('action') != 'finish':
            if not self.team_id or self.team_id not in [self.match.team1.id, self.match.team2.id]:
                return {'error': 'Invalid team ID', 'success': False}
        
        if self.match not in self.fixture.scheduled_matches.all():
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
            return {
                'success': True, 
                'message': 'Set completed, proceeding to next set or match completion'
            }
            
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
        
        return {'success': True, 'message': 'Match completed successfully'}
    
    def handle_match_completion(self):
        """Handle post-match completion tasks."""
        self.fixture.scheduled_matches.remove(self.match)
        
        if self.fixture.fixtureType == 'KO':
            self.handle_ko_completion()
        elif self.fixture.fixtureType == 'RR':
            self.handle_rr_completion()
    
    def handle_ko_completion(self):
        """Handle knockout tournament progression."""
        ko_instance = self.fixture.content_object
        ko_instance.winners_bracket.add(self.match.winner)
        ko_instance.save()
        
        if not ko_instance.bracket_matches.exists() and not self.fixture.scheduled_matches.exists():
            self.schedule_next_ko_stage(ko_instance)
    
    def handle_rr_completion(self):
        """Handle round robin statistics update."""
        rr_instance = self.fixture.content_object
        if hasattr(rr_instance, 'update_team_stats'):
            rr_instance.update_team_stats(self.match)
        rr_instance.save()
    
    def schedule_next_ko_stage(self, ko_instance):
        """Schedule next stage of knockout tournament."""
        winners = list(ko_instance.winners_bracket.all())
        ko_instance.bracket_teams.set(winners)
        ko_instance.winners_bracket.clear()
        
        if ko_instance.ko_stage == 1 and len(winners) == 1:
            self.category.winner = winners[0]
            self.category.save()
            return
        
        with transaction.atomic():
            stage_matches = ko_instance.all_matches.filter(
                stage_number=ko_instance.ko_stage
            ).order_by('match_number')
            
            match_num = 0
            for i in range(0, stage_matches.count(), 2):
                if i + 1 >= stage_matches.count():
                    break
                    
                match1 = stage_matches[i]
                match2 = stage_matches[i + 1]
                
                match = Match.objects.create(
                    category=self.category,
                    team1=match1.winner,
                    team2=match2.winner,
                    sport=self.match.sport,
                    match_number=match_num,
                    stage_number=ko_instance.ko_stage - 1
                )
                match_num += 1
                
                if self.sport.scoring_type == 'sets':
                    SetScore.objects.bulk_create([
                        SetScore(match=match, set_number=j + 1) 
                        for j in range(self.category.max_sets)
                    ])
                else:
                    SimpleScore.objects.create(match=match)
                    
                ko_instance.bracket_matches.add(match)
                ko_instance.all_matches.add(match)
            
            ko_instance.ko_stage -= 1
            ko_instance.save()

