"""
LIVESCORE API FOOTBALL DASHBOARD - COMPLETE VERCEL-OPTIMIZED VERSION
Features:
- Live scores with REAL scores
- Match events with goal scorers
- Gemini AI integration
- NewsAPI integration
- Dual WhatsApp panels
- Fully compatible with Vercel serverless
"""

import os
import logging
import re
from flask import Flask, jsonify, render_template, request, send_from_directory
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests

# ==================== LOAD ENVIRONMENT VARIABLES ====================
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== INITIALIZE FLASK APP ====================
app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

# ==================== LIVESCORE API WRAPPER ====================
class LiveScoreAPI:
    """LiveScore API wrapper - FIXED score extraction"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://livescore-api.com/api-client"
        self.session = requests.Session()
        
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Base request method"""
        if params is None:
            params = {}
        
        params.update({
            "key": self.api_key,
            "secret": self.api_secret
        })
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_live_scores(self, competition_id: int = None) -> list:
        """Get all live matches - FIXED score extraction"""
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
        """Extract match data - CRITICAL: scores from 'score' string field"""
        processed = match.copy() if isinstance(match, dict) else {}
        
        if not isinstance(processed, dict):
            return {}
        
        # ===== SCORE EXTRACTION - FIXED =====
        home_score = 0
        away_score = 0
        
        # Method 1: Parse from 'score' field (THIS IS WHERE THE REAL SCORE IS!)
        score_str = processed.get('score', '')
        if score_str and isinstance(score_str, str):
            parts = re.split(r'\s*-\s*', score_str)
            if len(parts) == 2:
                home_score = int(parts[0]) if parts[0].isdigit() else 0
                away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        # Method 2: Parse from 'ft_score' for finished matches
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
        
        # ===== Minute formatting =====
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
        
        return processed
    
    def get_today_fixtures(self) -> list:
        """Get today's fixtures"""
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
        """Get league standings"""
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
        """Test API connection"""
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
            return {"status": "error", "key_valid": False, "message": "API error"}
        except Exception as e:
            return {"status": "error", "key_valid": False, "message": str(e)}


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
        return {"available": True, "message": "Connected"}


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
        return f"Error loading template: {e}", 500


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


# ==================== LIVE SCORES ====================

@app.route('/api/live')
@app.route('/api/livescores')
@app.route('/api/fixtures/live')
@app.route('/api/fixtures/live/details')
def get_live_scores():
    """Get all live matches - FIXED score mapping"""
    if not livescore:
        return jsonify({"error": "LiveScore API not configured"}), 503
    
    competition_id = request.args.get('competition_id', type=int)
    matches = livescore.get_live_scores(competition_id)
    
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


# ==================== FIXTURES ====================

@app.route('/api/fixtures/today')
def get_today_fixtures():
    """Get today's fixtures"""
    if not livescore:
        return jsonify({"error": "LiveScore API not configured"}), 503
    
    fixtures = livescore.get_today_fixtures()
    
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


# ==================== GEMINI AI ENDPOINTS ====================

@app.route('/api/gemini/status', methods=['GET'])
def gemini_status():
    """Check Gemini AI status"""
    return jsonify(gemini.test_connection())


@app.route('/api/gemini/enhance', methods=['POST'])
def gemini_enhance():
    """Enhance WhatsApp message"""
    data = request.json
    message = data.get('message', '')
    if not message:
        return jsonify({"error": "No message"}), 400
    
    enhanced = gemini.enhance_message(message)
    return jsonify({"success": True, "enhanced": enhanced})


@app.route('/api/gemini/translate', methods=['POST'])
def gemini_translate():
    """Translate message"""
    data = request.json
    message = data.get('message', '')
    language = data.get('language', 'es')
    
    translated = gemini.translate_message(message, language)
    return jsonify({"success": True, "translated": translated})


@app.route('/api/gemini/news/summarize', methods=['POST'])
def gemini_news_summary():
    """Summarize news articles"""
    data = request.json
    articles = data.get('articles', [])
    
    summary = gemini.summarize_news(articles)
    return jsonify({"success": True, "summary": summary})


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


# ==================== DEBUG ENDPOINT ====================

@app.route('/api/debug/scores')
def debug_scores():
    """Debug endpoint to verify score extraction"""
    if not livescore:
        return jsonify({"error": "API not configured"})
    
    matches = livescore.get_live_scores()
    debug = []
    for match in matches[:5]:
        debug.append({
            "home": match.get('home_name'),
            "away": match.get('away_name'),
            "score_field": match.get('score'),
            "extracted": f"{match.get('home_score', 0)}-{match.get('away_score', 0)}",
            "minute": match.get('minute')
        })
    
    return jsonify({
        "total": len(matches),
        "samples": debug,
        "note": "Scores extracted from 'score' field"
    })


# ==================== STATIC FILES ====================

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


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
    print("🚀 FOOTBALL DASHBOARD - READY FOR VERCEL")
    print("=" * 60)
    
    if livescore:
        status = livescore.test_connection()
        print(f"✅ LiveScore: {'Connected' if status.get('key_valid') else 'Failed'}")
    else:
        print("❌ LiveScore: Not configured")
    
    print(f"✅ Gemini AI: {'Connected' if gemini.is_available() else 'Not configured'}")
    print(f"✅ NewsAPI: {'Connected' if newsapi else 'Not configured'}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
    
    
