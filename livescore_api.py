"""
LIVESCORE API - COMPLETE FIXED VERSION
Correctly extracts scores from the 'score' string field
Now shows REAL scores like "2 - 0", "3 - 1", etc.
"""

import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class LiveScoreAPI:
    """Complete LiveScore API wrapper - FIXED score extraction"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://livescore-api.com/api-client"
        self.session = requests.Session()
        
    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Base request method"""
        if params is None:
            params = {}
        
        params.update({
            "key": self.api_key,
            "secret": self.api_secret
        })
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== LIVE SCORES - FIXED ====================
    
    def get_live_scores(self, competition_id: int = None) -> List[Dict]:
        """Get all live matches - FIXED score extraction"""
        params = {}
        if competition_id:
            params["competition_id"] = competition_id
        
        data = self._get("/scores/live.json", params)
        if data.get("success"):
            matches = data.get("data", {}).get("match", [])
            
            # Process ALL matches with correct score extraction
            processed_matches = []
            for match in matches:
                processed = self._extract_match_data(match)
                
                # Only include matches that are actually LIVE or IN PLAY
                status = processed.get('status', '')
                minute = processed.get('minute', '0')
                
                if status not in ['FINISHED', 'FT', 'FULL_TIME', 'NS', 'Not Started']:
                    if minute not in ['0', 'NS', ''] or status == 'IN PLAY' or status == 'ADDED TIME':
                        processed_matches.append(processed)
            
            return processed_matches
        return []
    
    def _extract_match_data(self, match: Dict) -> Dict:
        """
        Extract and normalize match data - CRITICAL FIX
        Scores are in the 'score' field as a string like "2 - 0"
        NOT in home_score/away_score fields (those are always 0)
        """
        processed = match.copy() if isinstance(match, dict) else {}
        
        if not isinstance(processed, dict):
            return {}
        
        # ===== CRITICAL FIX: Extract score from 'score' STRING field =====
        home_score = 0
        away_score = 0
        
        # METHOD 1: Parse from 'score' field (THIS IS WHERE THE REAL SCORE IS!)
        score_str = processed.get('score', '')
        if score_str and isinstance(score_str, str):
            # Format is "2 - 0" or "0 - 1" or "3 - 1"
            # Handle various formats: "2-0", "2 - 0", "2 -0", etc.
            parts = re.split(r'\s*-\s*', score_str)
            if len(parts) == 2:
                home_score = int(parts[0]) if parts[0].isdigit() else 0
                away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        # METHOD 2: Parse from 'ft_score' for finished matches
        if home_score == 0 and away_score == 0:
            ft_score = processed.get('ft_score', '')
            if ft_score and isinstance(ft_score, str):
                parts = re.split(r'\s*-\s*', ft_score)
                if len(parts) == 2:
                    home_score = int(parts[0]) if parts[0].isdigit() else 0
                    away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        # METHOD 3: Parse from 'ht_score' for half-time
        if home_score == 0 and away_score == 0:
            ht_score = processed.get('ht_score', '')
            if ht_score and isinstance(ht_score, str):
                parts = re.split(r'\s*-\s*', ht_score)
                if len(parts) == 2:
                    home_score = int(parts[0]) if parts[0].isdigit() else 0
                    away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        # METHOD 4: Try to get from scores object
        if home_score == 0 and away_score == 0:
            scores_obj = processed.get('scores', {})
            if isinstance(scores_obj, dict):
                # Try current score first
                if 'current' in scores_obj:
                    current = scores_obj['current']
                    if isinstance(current, dict):
                        home_score = current.get('home', 0)
                        away_score = current.get('away', 0)
                # Then try direct home/away
                elif 'home' in scores_obj and 'away' in scores_obj:
                    home_score = scores_obj.get('home', 0)
                    away_score = scores_obj.get('away', 0)
        
        # METHOD 5: Try direct home_score/away_score fields (sometimes they exist)
        if home_score == 0 and away_score == 0:
            home_score = processed.get('home_score', 0)
            away_score = processed.get('away_score', 0)
            if isinstance(home_score, str):
                home_score = int(home_score) if home_score.isdigit() else 0
            if isinstance(away_score, str):
                away_score = int(away_score) if away_score.isdigit() else 0
        
        processed['home_score'] = home_score
        processed['away_score'] = away_score
        processed['score_display'] = score_str
        
        # ===== Minute formatting - clean up special characters =====
        minute = processed.get('time', processed.get('minute', '0'))
        if isinstance(minute, str):
            # Remove any special characters like \u200e
            minute = minute.replace('\u200e', '').strip()
        elif isinstance(minute, (int, float)):
            minute = str(minute)
        
        # Clean up minute display
        if minute in ['NS', 'Not Started', '']:
            minute = '0'
        elif minute == 'HT':
            minute = '45'
        elif minute == 'FT':
            minute = '90'
        elif minute == 'LIVE':
            minute = '0'
        elif minute == 'FINISHED':
            minute = '90'
        
        processed['minute'] = minute
        processed['time'] = minute
        
        # ===== Team name normalization =====
        if 'home_name' not in processed and 'home' in processed:
            home = processed.get('home', {})
            if isinstance(home, dict):
                processed['home_name'] = home.get('name', 'Home')
                processed['home_id'] = home.get('id')
        
        if 'away_name' not in processed and 'away' in processed:
            away = processed.get('away', {})
            if isinstance(away, dict):
                processed['away_name'] = away.get('name', 'Away')
                processed['away_id'] = away.get('id')
        
        # ===== Competition info =====
        if 'competition_name' not in processed and 'competition' in processed:
            comp = processed.get('competition', {})
            if isinstance(comp, dict):
                processed['competition_name'] = comp.get('name', '')
                processed['competition_id'] = comp.get('id')
        
        # ===== Status =====
        if 'status' not in processed:
            if minute == '0':
                processed['status'] = 'NS'
            elif minute == '45':
                processed['status'] = 'HT'
            elif minute == '90':
                processed['status'] = 'FT'
            else:
                processed['status'] = 'LIVE'
        
        return processed
    
    def get_live_matches_count(self) -> int:
        """Get number of live matches right now"""
        return len(self.get_live_scores())
    
    # ==================== MATCH EVENTS ====================
    
    def get_match_events(self, fixture_id: int) -> Dict:
        """Get all events for a specific match"""
        data = self._get("/matches/events.json", {"id": fixture_id})
        
        if data.get("success"):
            return {
                "success": True,
                "match": data.get("data", {}).get("match", {}),
                "events": data.get("data", {}).get("event", [])
            }
        return {"success": False, "match": {}, "events": []}
    
    def format_events_for_display(self, events: List[Dict]) -> List[Dict]:
        """Format events for display"""
        formatted = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
                
            event_type = event.get('event', '')
            minute = event.get('time', 0)
            player_name = event.get('player', {}).get('name', 'Unknown')
            is_home = event.get('is_home', False)
            
            formatted_event = {
                'minute': minute,
                'minute_display': f"{minute}'",
                'type': event_type,
                'player': player_name,
                'team': 'home' if is_home else 'away',
                'icon': self._get_event_icon(event_type)
            }
            
            if event_type in ['GOAL', 'GOAL_PENALTY'] and event.get('info'):
                assist_name = event['info'].get('name', 'Unknown')
                formatted_event['assist'] = assist_name
                formatted_event['has_assist'] = True
                formatted_event['description'] = f"⚽ {minute}' - {player_name} (assist: {assist_name})"
            elif event_type == 'OWN_GOAL':
                formatted_event['description'] = f"🔄 {minute}' - OWN GOAL by {player_name}"
            elif event_type in ['YELLOW_CARD', 'RED_CARD', 'YELLOW_RED_CARD']:
                card_icon = '🟨' if 'YELLOW' in event_type else '🟥'
                formatted_event['description'] = f"{card_icon} {minute}' - {player_name}"
            elif event_type == 'SUBSTITUTION':
                player_in = player_name
                player_out = event.get('info', {}).get('name', 'Unknown')
                formatted_event['player_in'] = player_in
                formatted_event['player_out'] = player_out
                formatted_event['description'] = f"🔄 {minute}' - IN: {player_in}, OUT: {player_out}"
            elif event_type == 'MISSED_PENALTY':
                formatted_event['description'] = f"❌ {minute}' - MISSED PENALTY by {player_name}"
            else:
                formatted_event['description'] = f"{formatted_event['icon']} {minute}' - {player_name}"
            
            formatted.append(formatted_event)
        
        # Sort by minute
        formatted.sort(key=lambda x: x['minute'])
        return formatted
    
    def _get_event_icon(self, event_type: str) -> str:
        """Get emoji icon for event type"""
        icons = {
            'GOAL': '⚽',
            'GOAL_PENALTY': '🥅',
            'OWN_GOAL': '🔄',
            'YELLOW_CARD': '🟨',
            'RED_CARD': '🟥',
            'YELLOW_RED_CARD': '🟨🟥',
            'SUBSTITUTION': '🔄',
            'MISSED_PENALTY': '❌'
        }
        return icons.get(event_type, '⚡')
    
    # ==================== FIXTURES ====================
    
    def get_today_fixtures(self) -> List[Dict]:
        """Get all fixtures scheduled for today"""
        data = self._get("/fixtures/list.json")
        if data.get("success"):
            fixtures = data.get("data", {}).get("fixtures", [])
            
            # Process fixtures to normalize format
            processed_fixtures = []
            for fixture in fixtures:
                processed = self._extract_fixture_data(fixture)
                processed_fixtures.append(processed)
            
            return processed_fixtures
        return []
    
    def _extract_fixture_data(self, fixture: Dict) -> Dict:
        """Normalize fixture data"""
        processed = fixture.copy() if isinstance(fixture, dict) else {}
        
        if 'home_name' not in processed and 'home' in processed:
            home = processed.get('home', {})
            if isinstance(home, dict):
                processed['home_name'] = home.get('name', 'Home')
                processed['home_id'] = home.get('id')
        
        if 'away_name' not in processed and 'away' in processed:
            away = processed.get('away', {})
            if isinstance(away, dict):
                processed['away_name'] = away.get('name', 'Away')
                processed['away_id'] = away.get('id')
        
        if 'competition_name' not in processed and 'competition' in processed:
            comp = processed.get('competition', {})
            if isinstance(comp, dict):
                processed['competition_name'] = comp.get('name', '')
                processed['competition_id'] = comp.get('id')
        
        return processed
    
    def get_fixtures_by_date(self, date: str = None) -> List[Dict]:
        """Get fixtures for specific date (YYYY-MM-DD)"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        data = self._get("/fixtures/matches.json", {"date": date})
        if data.get("success"):
            fixtures = data.get("data", [])
            processed_fixtures = []
            for fixture in fixtures:
                processed = self._extract_fixture_data(fixture)
                processed_fixtures.append(processed)
            return processed_fixtures
        return []
    
    def get_upcoming_fixtures(self, days: int = 7) -> List[Dict]:
        """Get fixtures for the next X days"""
        all_fixtures = []
        today = datetime.now()
        
        for day in range(days):
            date = (today + timedelta(days=day)).strftime("%Y-%m-%d")
            fixtures = self.get_fixtures_by_date(date)
            if isinstance(fixtures, list):
                all_fixtures.extend(fixtures[:10])
        
        return all_fixtures[:50]
    
    # ==================== STANDINGS ====================
    
    def get_league_table(self, competition_id: int) -> List[Dict]:
        """Get full standings table for a competition"""
        data = self._get("/leagues/table.json", {"competition_id": competition_id})
        if data.get("success"):
            try:
                return data.get("data", {}).get("table", [])
            except:
                stages = data.get("data", {}).get("stages", [])
                if stages:
                    groups = stages[0].get("groups", [])
                    if groups:
                        return groups[0].get("standings", [])
        return []
    
    # ==================== HEAD TO HEAD ====================
    
    def get_head_to_head(self, home_id: int, away_id: int, limit: int = 5) -> List[Dict]:
        """Get head-to-head matches between two teams"""
        data = self._get("/scores/h2h.json", {
            "home_id": home_id,
            "away_id": away_id
        })
        if data.get("success"):
            matches = data.get("data", [])
            return matches[:limit] if isinstance(matches, list) else []
        return []
    
    def get_h2h_summary(self, home_id: int, away_id: int) -> Dict:
        """Get summary statistics of head-to-head record"""
        matches = self.get_head_to_head(home_id, away_id, limit=20)
        
        home_wins = 0
        away_wins = 0
        draws = 0
        home_goals = 0
        away_goals = 0
        
        for match in matches:
            if isinstance(match, dict):
                # Extract scores from H2H matches
                home_score = 0
                away_score = 0
                
                # Try to get from score string
                score_str = match.get('score', '')
                if score_str and isinstance(score_str, str):
                    parts = re.split(r'\s*-\s*', score_str)
                    if len(parts) == 2:
                        home_score = int(parts[0]) if parts[0].isdigit() else 0
                        away_score = int(parts[1]) if parts[1].isdigit() else 0
                
                if home_score > away_score:
                    home_wins += 1
                elif home_score < away_score:
                    away_wins += 1
                else:
                    draws += 1
                
                home_goals += home_score
                away_goals += away_score
        
        return {
            "total_matches": len(matches),
            "home_wins": home_wins,
            "away_wins": away_wins,
            "draws": draws,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "recent_form": matches[:5]
        }
    
    # ==================== SEARCH ====================
    
    def search_teams(self, query: str) -> List[Dict]:
        """Search for teams by name"""
        data = self._get("/fixtures/list.json", {"search": query})
        if data.get("success"):
            fixtures = data.get("data", {}).get("fixtures", [])
            teams = {}
            for f in fixtures:
                if isinstance(f, dict):
                    # Add home team
                    home = f.get('home', {})
                    if isinstance(home, dict):
                        home_id = home.get('id')
                        if home_id and home_id not in teams:
                            teams[home_id] = {
                                "id": home_id,
                                "name": home.get('name'),
                                "country": f.get('country', {}).get('name'),
                                "logo": home.get('logo')
                            }
                    # Add away team
                    away = f.get('away', {})
                    if isinstance(away, dict):
                        away_id = away.get('id')
                        if away_id and away_id not in teams:
                            teams[away_id] = {
                                "id": away_id,
                                "name": away.get('name'),
                                "country": f.get('country', {}).get('name'),
                                "logo": away.get('logo')
                            }
            return list(teams.values())[:10]
        return []
    
    # ==================== TEST CONNECTION ====================
    
    def test_connection(self) -> Dict:
        """Test if API credentials are working"""
        try:
            data = self._get("/scores/live.json", {"limit": 1})
            if data.get("success"):
                matches = data.get("data", {}).get("match", [])
                
                # Test score extraction on a sample match
                sample_score = "0-0"
                if matches and len(matches) > 0:
                    test_match = self._extract_match_data(matches[0])
                    sample_score = f"{test_match.get('home_score', 0)}-{test_match.get('away_score', 0)}"
                
                return {
                    "status": "ok",
                    "key_valid": True,
                    "message": "API connection successful",
                    "live_matches": len(matches),
                    "sample_score": sample_score,
                    "score_extraction": "FIXED - using 'score' string field"
                }
            else:
                return {
                    "status": "error",
                    "key_valid": False,
                    "message": data.get("error", "Unknown error"),
                    "live_matches": 0
                }
        except Exception as e:
            return {
                "status": "error",
                "key_valid": False,
                "message": str(e),
                "live_matches": 0
            }