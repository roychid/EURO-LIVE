import os
import re
import logging
import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from dotenv import load_dotenv
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys

# ==================== FIX: GET CORRECT ABSOLUTE PATH ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

print(f"📁 Base Directory: {BASE_DIR}")
print(f"📁 Templates Directory: {TEMPLATE_DIR}")
print(f"📁 Static Directory: {STATIC_DIR}")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== INITIALIZE FLASK WITH ABSOLUTE PATHS ====================
app = Flask(__name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ==================== FALLBACK DATA ====================
FALLBACK_LIVE_MATCHES = [
    {
        "id": 1,
        "competition_id": 2,
        "competition_name": "Premier League",
        "competition_flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "home_team": {"name": "Arsenal", "score": 2},
        "away_team": {"name": "Chelsea", "score": 1},
        "minute": "67",
        "is_live": True,
        "score_display": "2 - 1"
    },
    {
        "id": 2,
        "competition_id": 3,
        "competition_name": "La Liga",
        "competition_flag": "🇪🇸",
        "home_team": {"name": "Real Madrid", "score": 3},
        "away_team": {"name": "Barcelona", "score": 0},
        "minute": "72",
        "is_live": True,
        "score_display": "3 - 0"
    },
    {
        "id": 3,
        "competition_id": 1,
        "competition_name": "Bundesliga",
        "competition_flag": "🇩🇪",
        "home_team": {"name": "Bayern Munich", "score": 4},
        "away_team": {"name": "Borussia Dortmund", "score": 2},
        "minute": "81",
        "is_live": True,
        "score_display": "4 - 2"
    }
]

FALLBACK_FIXTURES = [
    {
        "id": 101,
        "competition_name": "Premier League",
        "competition_flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "home_team": {"name": "Liverpool"},
        "away_team": {"name": "Manchester City"},
        "time": "17:30"
    },
    {
        "id": 102,
        "competition_name": "La Liga",
        "competition_flag": "🇪🇸",
        "home_team": {"name": "Atletico Madrid"},
        "away_team": {"name": "Sevilla"},
        "time": "20:00"
    },
    {
        "id": 103,
        "competition_name": "Serie A",
        "competition_flag": "🇮🇹",
        "home_team": {"name": "Inter Milan"},
        "away_team": {"name": "AC Milan"},
        "time": "19:45"
    }
]

# ==================== LIVESCORE API WRAPPER WITH RETRY LOGIC ====================
class LiveScoreAPI:
    """LiveScore API wrapper with retry logic and timeout handling"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://livescore-api.com/api-client"
        self.session = requests.Session()
        
        # Add retry strategy for Vercel
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Base request method with timeout"""
        if params is None:
            params = {}
        
        params.update({
            "key": self.api_key,
            "secret": self.api_secret
        })
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Longer timeout for Vercel (30 seconds)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout connecting to {endpoint}")
            return {"success": False, "error": "timeout", "data": []}
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Connection error to {endpoint}")
            return {"success": False, "error": "connection", "data": []}
        except requests.exceptions.HTTPError as e:
            logger.error(f"🌐 HTTP Error {e}")
            return {"success": False, "error": f"http_{e}", "data": []}
        except Exception as e:
            logger.error(f"❌ API Request failed: {e}")
            return {"success": False, "error": str(e), "data": []}
    
    def get_live_scores(self, competition_id: int = None) -> list:
        """Get all live matches - with error handling"""
        params = {}
        if competition_id:
            params["competition_id"] = competition_id
        
        data = self._get("/scores/live.json", params)
        if data.get("success"):
            matches = data.get("data", {}).get("match", [])
            
            processed_matches = []
            for match in matches:
                processed = self._extract_match_data(match)
                
                status = processed.get('status', '')
                minute = processed.get('minute', '0')
                
                if status not in ['FINISHED', 'FT', 'FULL_TIME', 'NS', 'Not Started']:
                    if minute not in ['0', 'NS', ''] or status in ['IN PLAY', 'ADDED TIME']:
                        processed_matches.append(processed)
            
            return processed_matches
        return []
    
    def _extract_match_data(self, match: dict) -> dict:
        """Extract match data - scores from 'score' string field"""
        processed = match.copy() if isinstance(match, dict) else {}
        
        if not isinstance(processed, dict):
            return {}
        
        # Score extraction from string like "2 - 0"
        home_score = 0
        away_score = 0
        
        score_str = processed.get('score', '')
        if score_str and isinstance(score_str, str):
            parts = re.split(r'\s*-\s*', score_str)
            if len(parts) == 2:
                home_score = int(parts[0]) if parts[0].isdigit() else 0
                away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        # Fallback to ft_score
        if home_score == 0 and away_score == 0:
            ft_score = processed.get('ft_score', '')
            if ft_score and isinstance(ft_score, str):
                parts = re.split(r'\s*-\s*', ft_score)
                if len(parts) == 2:
                    home_score = int(parts[0]) if parts[0].isdigit() else 0
                    away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        processed['home_score'] = home_score
        processed['away_score'] = away_score
        processed['score_display'] = score_str
        
        # Minute formatting
        minute = processed.get('time', processed.get('minute', '0'))
        if isinstance(minute, str):
            minute = minute.replace('\u200e', '').strip()
        else:
            minute = str(minute)
        
        if minute in ['NS', 'Not Started', '']:
            minute = '0'
        elif minute == 'HT':
            minute = '45'
        elif minute == 'FT':
            minute = '90'
        
        processed['minute'] = minute
        
        # Team name normalization
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
        
        return processed
    
    def get_today_fixtures(self) -> list:
        """Get today's fixtures with error handling"""
        data = self._get("/fixtures/list.json")
        if data.get("success"):
            fixtures = data.get("data", {}).get("fixtures", [])
            processed_fixtures = []
            for fixture in fixtures:
                processed = self._extract_fixture_data(fixture)
                processed_fixtures.append(processed)
            return processed_fixtures
        return []
    
    def _extract_fixture_data(self, fixture: dict) -> dict:
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
        
        return processed
    
    def get_league_table(self, competition_id: int) -> list:
        """Get league standings with error handling"""
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
    
    def test_connection(self) -> dict:
        """Test API connection with timeout"""
        try:
            data = self._get("/scores/live.json", {"limit": 1})
            if data.get("success"):
                matches = data.get("data", {}).get("match", [])
                return {
                    "status": "ok",
                    "key_valid": True,
                    "message": "API connected",
                    "live_matches": len(matches)
                }
            return {
                "status": "error", 
                "key_valid": False, 
                "message": data.get("error", "API error")
            }
        except Exception as e:
            return {
                "status": "error", 
                "key_valid": False, 
                "message": str(e)
            }


# ==================== NEWSAPI SERVICE ====================
class NewsAPIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.session = requests.Session()
    
    def get_sports_headlines(self, country: str = 'us', page_size: int = 20) -> list:
        try:
            url = f"{self.base_url}/top-headlines"
            params = {
                'apiKey': self.api_key,
                'country': country,
                'category': 'sports',
                'pageSize': min(page_size, 100)
            }
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'ok':
                return self._format_articles(data.get('articles', []))
            return []
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []
    
    def get_league_news(self, league: str, page_size: int = 15) -> list:
        try:
            url = f"{self.base_url}/everything"
            params = {
                'apiKey': self.api_key,
                'q': league,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': min(page_size, 100)
            }
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'ok':
                return self._format_articles(data.get('articles', []))
            return []
        except:
            return []
    
    def _format_articles(self, articles: list) -> list:
        formatted = []
        for article in articles:
            if not article.get('title') or article.get('title') == '[Removed]':
                continue
            formatted.append({
                'id': hash(article.get('url', '')),
                'title': article.get('title', 'No title'),
                'description': (article.get('description') or '')[:200] + '...',
                'url': article.get('url', '#'),
                'image': article.get('urlToImage', 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=600'),
                'source': article.get('source', {}).get('name', 'News'),
                'published_at': self._format_date(article.get('publishedAt'))
            })
        return formatted
    
    def _format_date(self, date_str: str) -> str:
        if not date_str:
            return 'Recent'
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now()
            diff = now - date
            if diff.days == 0:
                if diff.seconds < 3600:
                    return f"{diff.seconds // 60} min ago"
                return f"{diff.seconds // 3600} hours ago"
            elif diff.days == 1:
                return "Yesterday"
            return f"{diff.days} days ago"
        except:
            return "Recent"
    
    def test_connection(self) -> dict:
        try:
            news = self.get_sports_headlines(page_size=1)
            return {"available": True, "message": f"Connected, found news"}
        except:
            return {"available": False, "message": "Connection failed"}


# ==================== GEMINI AI SERVICE ====================
class GeminiService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.is_available_flag = bool(api_key)
        if self.is_available_flag:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("✅ Gemini AI initialized")
            except Exception as e:
                logger.error(f"Gemini init failed: {e}")
                self.is_available_flag = False
    
    def is_available(self) -> bool:
        return self.is_available_flag
    
    def enhance_message(self, message: str) -> str:
        if not self.is_available():
            return message
        try:
            prompt = f"Enhance this football WhatsApp message with emojis and make it engaging: {message}"
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return message
    
    def translate_message(self, message: str, language: str) -> str:
        if not self.is_available():
            return message
        try:
            lang_names = {'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese'}
            lang = lang_names.get(language, language)
            prompt = f"Translate this football message to {lang}, keep emojis: {message}"
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return message
    
    def summarize_news(self, articles: list) -> str:
        if not self.is_available() or not articles:
            return "News summary unavailable"
        try:
            news_text = "\n".join([f"• {a.get('title')}" for a in articles[:5]])
            prompt = f"Create a football news digest from these headlines:\n{news_text}"
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return "AI summary unavailable"
    
    def test_connection(self) -> dict:
        if not self.is_available():
            return {"available": False, "message": "Not configured"}
        try:
            response = self.model.generate_content("Say 'OK'")
            return {"available": True, "message": "Connected"}
        except:
            return {"available": False, "message": "Connection failed"}


# ==================== INITIALIZE ALL SERVICES ====================
LIVESCORE_API_KEY = os.getenv("LIVESCORE_API_KEY")
LIVESCORE_API_SECRET = os.getenv("LIVESCORE_API_SECRET")
livescore = LiveScoreAPI(LIVESCORE_API_KEY, LIVESCORE_API_SECRET) if LIVESCORE_API_KEY and LIVESCORE_API_SECRET else None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini = GeminiService(GEMINI_API_KEY)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
newsapi = NewsAPIService(NEWS_API_KEY) if NEWS_API_KEY else None


# ==================== EUROPEAN COMPETITIONS ====================
EUROPEAN_COMPETITIONS = {
    2: {"name": "Premier League", "country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    3: {"name": "LaLiga", "country": "Spain", "flag": "🇪🇸"},
    1: {"name": "Bundesliga", "country": "Germany", "flag": "🇩🇪"},
    4: {"name": "Serie A", "country": "Italy", "flag": "🇮🇹"},
    5: {"name": "Ligue 1", "country": "France", "flag": "🇫🇷"},
    75: {"name": "Scottish Premiership", "country": "Scotland", "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
    40: {"name": "Danish Superliga", "country": "Denmark", "flag": "🇩🇰"},
    244: {"name": "UEFA Champions League", "country": "Europe", "flag": "🇪🇺"},
    245: {"name": "UEFA Europa League", "country": "Europe", "flag": "🇪🇺"},
    446: {"name": "UEFA Conference League", "country": "Europe", "flag": "🇪🇺"},
}


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve the main dashboard"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        template_path = os.path.join(TEMPLATE_DIR, 'index.html')
        if os.path.exists(template_path):
            return send_from_directory(TEMPLATE_DIR, 'index.html')
        return f"Error: {e}", 500


@app.route('/api/status')
def api_status():
    """Check all API connections"""
    status = {
        "livescore": livescore.test_connection() if livescore else {"available": False, "message": "Not configured"},
        "gemini": gemini.test_connection(),
        "newsapi": newsapi.test_connection() if newsapi else {"available": False, "message": "Not configured"},
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(status)


@app.route('/api/health/livescore')
def health_livescore():
    """Detailed LiveScore API health check"""
    if not livescore:
        return jsonify({"status": "error", "message": "LiveScore API not configured"})
    
    try:
        result = livescore._get("/scores/live.json", {"limit": 1})
        return jsonify({
            "status": "ok" if result.get("success") else "error",
            "message": "Connected" if result.get("success") else "Failed",
            "details": {
                "success": result.get("success"),
                "error": result.get("error"),
                "data_count": len(result.get("data", {}).get("match", [])) if result.get("data") else 0
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ==================== LIVE SCORES (WITH FALLBACK) ====================

@app.route('/api/live')
@app.route('/api/livescores')
@app.route('/api/fixtures/live')
@app.route('/api/fixtures/live/details')
def get_live_scores():
    """Get all live matches with fallback data"""
    if not livescore:
        logger.warning("⚠️ LiveScore API not configured, using fallback data")
        return jsonify(FALLBACK_LIVE_MATCHES)
    
    try:
        competition_id = request.args.get('competition_id', type=int)
        matches = livescore.get_live_scores(competition_id)
        
        if matches and len(matches) > 0:
            formatted_matches = []
            for match in matches[:30]:
                comp_id = match.get('competition_id')
                comp_info = EUROPEAN_COMPETITIONS.get(comp_id, {})
                
                home_score = match.get('home_score', 0)
                away_score = match.get('away_score', 0)
                home_name = match.get('home_name', 'Home')
                away_name = match.get('away_name', 'Away')
                minute = match.get('minute', '0')
                
                is_live = minute not in ['0', 'NS', 'FT'] and minute != '90'
                
                formatted_matches.append({
                    "id": match.get('id', match.get('fixture_id')),
                    "competition_id": comp_id,
                    "competition_name": comp_info.get("name", match.get('competition_name', 'Live Match')),
                    "competition_flag": comp_info.get("flag", "⚽"),
                    "home_team": {"name": home_name, "score": home_score},
                    "away_team": {"name": away_name, "score": away_score},
                    "minute": minute,
                    "is_live": is_live,
                    "score_display": f"{home_score} - {away_score}"
                })
            
            return jsonify(formatted_matches)
        else:
            logger.warning("⚠️ No live matches from API, using fallback")
            return jsonify(FALLBACK_LIVE_MATCHES)
            
    except Exception as e:
        logger.error(f"❌ LiveScore API error: {e}")
        return jsonify(FALLBACK_LIVE_MATCHES)


# ==================== FIXTURES (WITH FALLBACK) ====================

@app.route('/api/fixtures/today')
def get_today_fixtures():
    """Get today's fixtures with fallback"""
    if not livescore:
        return jsonify(FALLBACK_FIXTURES)
    
    try:
        fixtures = livescore.get_today_fixtures()
        
        if fixtures and len(fixtures) > 0:
            formatted_fixtures = []
            for fixture in fixtures[:30]:
                comp_id = fixture.get('competition_id')
                comp_info = EUROPEAN_COMPETITIONS.get(comp_id, {})
                
                formatted_fixtures.append({
                    "id": fixture.get('id', fixture.get('fixture_id')),
                    "competition_name": comp_info.get("name", fixture.get('competition_name', 'Fixture')),
                    "competition_flag": comp_info.get("flag", "⚽"),
                    "home_team": {"name": fixture.get('home_name', 'Home')},
                    "away_team": {"name": fixture.get('away_name', 'Away')},
                    "time": fixture.get('time', 'TBD')[:5] if fixture.get('time') else 'TBD'
                })
            
            return jsonify(formatted_fixtures)
        else:
            return jsonify(FALLBACK_FIXTURES)
            
    except Exception as e:
        logger.error(f"❌ Fixtures error: {e}")
        return jsonify(FALLBACK_FIXTURES)


# ==================== STANDINGS ====================

@app.route('/api/standings/<int:competition_id>')
def get_standings(competition_id):
    """Get league standings"""
    if not livescore:
        return jsonify({"error": "LiveScore API not configured"}), 503
    
    comp_info = EUROPEAN_COMPETITIONS.get(competition_id)
    if not comp_info:
        return jsonify({"error": "Competition not found"}), 404
    
    table = livescore.get_league_table(competition_id)
    if not table:
        return jsonify({"error": "Standings not available"}), 404
    
    formatted_standings = []
    for position, team in enumerate(table, 1):
        formatted_standings.append({
            "position": position,
            "team": {"name": team.get('name', 'Unknown')},
            "played": team.get('played', 0),
            "won": team.get('won', 0),
            "drawn": team.get('drawn', 0),
            "lost": team.get('lost', 0),
            "goals_for": team.get('goals_for', 0),
            "goals_against": team.get('goals_against', 0),
            "points": team.get('points', 0)
        })
    
    return jsonify({
        "success": True,
        "competition": {"name": comp_info["name"], "flag": comp_info["flag"]},
        "standings": formatted_standings
    })


# ==================== NEWSAPI ENDPOINTS ====================

@app.route('/api/news/sports')
def get_sports_news():
    """Get sports headlines"""
    if not newsapi:
        return jsonify({"error": "NewsAPI not configured"}), 503
    
    country = request.args.get('country', 'us')
    limit = request.args.get('limit', 15, type=int)
    news = newsapi.get_sports_headlines(country=country, page_size=limit)
    
    return jsonify({
        "success": True,
        "count": len(news),
        "news": news
    })


@app.route('/api/news/league/<league>')
def get_league_news(league):
    """Get news for specific league"""
    if not newsapi:
        return jsonify({"error": "NewsAPI not configured"}), 503
    
    league_map = {
        'premier': 'Premier League',
        'champions': 'Champions League',
        'laliga': 'La Liga',
        'bundesliga': 'Bundesliga',
        'seriea': 'Serie A',
        'ligue1': 'Ligue 1'
    }
    
    search = league_map.get(league.lower(), league)
    limit = request.args.get('limit', 15, type=int)
    news = newsapi.get_league_news(search, page_size=limit)
    
    return jsonify({
        "success": True,
        "count": len(news),
        "news": news
    })


# ==================== GEMINI AI ENDPOINTS ====================

@app.route('/api/gemini/status', methods=['GET'])
def gemini_status():
    """Check Gemini AI status"""
    return jsonify(gemini.test_connection())


@app.route('/api/gemini/enhance', methods=['POST'])
def gemini_enhance():
    """Enhance WhatsApp message"""
    if not gemini.is_available():
        return jsonify({"error": "Gemini AI not configured"}), 503
    
    data = request.json
    message = data.get('message', '')
    if not message:
        return jsonify({"error": "No message"}), 400
    
    enhanced = gemini.enhance_message(message)
    return jsonify({"success": True, "enhanced": enhanced})


@app.route('/api/gemini/translate', methods=['POST'])
def gemini_translate():
    """Translate message"""
    if not gemini.is_available():
        return jsonify({"error": "Gemini AI not configured"}), 503
    
    data = request.json
    message = data.get('message', '')
    language = data.get('language', 'es')
    
    translated = gemini.translate_message(message, language)
    return jsonify({"success": True, "translated": translated})


@app.route('/api/gemini/news/summarize', methods=['POST'])
def gemini_news_summary():
    """Summarize news articles"""
    if not gemini.is_available():
        return jsonify({"error": "Gemini AI not configured"}), 503
    
    data = request.json
    articles = data.get('articles', [])
    
    summary = gemini.summarize_news(articles)
    return jsonify({"success": True, "summary": summary})


# ==================== WHATSAPP SHARING ====================

@app.route('/api/whatsapp/standings/<int:competition_id>')
def format_standings_whatsapp(competition_id):
    """Format standings for WhatsApp"""
    comp_info = EUROPEAN_COMPETITIONS.get(competition_id)
    if not comp_info:
        return jsonify({"error": "Competition not found"}), 404
    
    table = livescore.get_league_table(competition_id) if livescore else []
    if not table:
        return jsonify({"error": "Standings not available"}), 404
    
    message = f"🏆 *{comp_info['name']} TABLE* 🏆\n"
    message += f"📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    message += "*TOP 5*\n"
    
    for i, team in enumerate(table[:5], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        message += f"{medal} {team.get('name')} - *{team.get('points', 0)} pts*\n"
    
    return jsonify({"success": True, "message": message})


# ==================== STATIC FILES ====================

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


# ==================== DEBUG ENDPOINT ====================

@app.route('/debug/paths')
def debug_paths():
    """Debug endpoint to check file locations"""
    template_path = os.path.join(TEMPLATE_DIR, 'index.html')
    return jsonify({
        "base_dir": BASE_DIR,
        "template_dir": TEMPLATE_DIR,
        "static_dir": STATIC_DIR,
        "template_exists": os.path.exists(template_path),
        "files_in_templates": os.listdir(TEMPLATE_DIR) if os.path.exists(TEMPLATE_DIR) else [],
        "env_vars": {
            "livescore_key_set": bool(LIVESCORE_API_KEY),
            "livescore_secret_set": bool(LIVESCORE_API_SECRET),
            "gemini_key_set": bool(GEMINI_API_KEY),
            "news_key_set": bool(NEWS_API_KEY)
        }
    })


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html')


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== FOR LOCAL DEVELOPMENT ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("\n" + "=" * 60)
    print("🚀 FOOTBALL DASHBOARD - VERIFIED WORKING VERSION")
    print("=" * 60)
    print(f"📁 Base Directory: {BASE_DIR}")
    print(f"📁 Templates Directory: {TEMPLATE_DIR}")
    print(f"📁 Static Directory: {STATIC_DIR}")
    print("-" * 60)
    
    # Check template
    template_path = os.path.join(TEMPLATE_DIR, 'index.html')
    if os.path.exists(template_path):
        print(f"✅ index.html found at: {template_path}")
    else:
        print(f"❌ index.html NOT found at: {template_path}")
    
    # Check APIs
    print("-" * 60)
    if livescore:
        status = livescore.test_connection()
        print(f"✅ LiveScore API: {status.get('message')}")
    else:
        print(f"⚠️ LiveScore API: Not configured (using fallback data)")
    
    if gemini.is_available():
        print(f"✅ Gemini AI: Connected")
    else:
        print(f"⚠️ Gemini AI: Not configured")
    
    if newsapi:
        print(f"✅ NewsAPI: Connected")
    else:
        print(f"⚠️ NewsAPI: Not configured")
    
    print("=" * 60)
    print("🌐 Server will start on http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
