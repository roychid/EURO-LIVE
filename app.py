"""
LIVESCORE API FOOTBALL DASHBOARD - COMPLETE FIXED VERSION
With Gemini AI integration and match data helper
"""

import os
import logging
from flask import Flask, jsonify, render_template, request, send_from_directory
from dotenv import load_dotenv
from datetime import datetime
from livescore_api import LiveScoreAPI
from gemini_service import GeminiService
from news_service import NewsAPIService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-this')

# ==================== INITIALIZE APIS ====================
LIVESCORE_API_KEY = os.getenv('LIVESCORE_API_KEY')
LIVESCORE_API_SECRET = os.getenv('LIVESCORE_API_SECRET')
livescore = LiveScoreAPI(LIVESCORE_API_KEY, LIVESCORE_API_SECRET)

# Initialize Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini = GeminiService(GEMINI_API_KEY)

# ==================== NEWSAPI INITIALIZATION ====================
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "e8a981afc6ca49399c4088f951a6318e")
newsapi = NewsAPIService(NEWS_API_KEY)

# ==================== NEWSAPI ENDPOINTS ====================

@app.route('/api/news/status')
def news_status():
    """Check NewsAPI connection"""
    try:
        # Quick test
        newsapi.get_sports_headlines(page_size=1)
        return jsonify({
            "status": "connected",
            "message": "NewsAPI is working",
            "key": f"{NEWS_API_KEY[:8]}...{NEWS_API_KEY[-8:]}"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 503

@app.route('/api/news/sports')
def get_sports_news():
    """Get sports headlines - PERFECT for ticker"""
    country = request.args.get('country', 'us')
    limit = request.args.get('limit', 10, type=int)
    news = newsapi.get_sports_headlines(country=country, page_size=limit)
    return jsonify({
        "success": True,
        "count": len(news),
        "news": news,
        "type": "sports_headlines"
    })

@app.route('/api/news/football')
def get_football_news():
    """Get general football news"""
    limit = request.args.get('limit', 15, type=int)
    news = newsapi.get_football_news(page_size=limit)
    return jsonify({
        "success": True,
        "count": len(news),
        "news": news,
        "type": "football_news"
    })

@app.route('/api/news/league/<league>')
def get_league_news(league):
    """Get news for specific league"""
    limit = request.args.get('limit', 15, type=int)
    
    # Common league names
    leagues = {
        'premier': 'Premier League',
        'premier-league': 'Premier League',
        'epl': 'Premier League',
        'laliga': 'La Liga',
        'la-liga': 'La Liga',
        'bundesliga': 'Bundesliga',
        'seriea': 'Serie A',
        'serie-a': 'Serie A',
        'ligue1': 'Ligue 1',
        'ligue-1': 'Ligue 1',
        'champions': 'Champions League',
        'champions-league': 'Champions League',
        'ucl': 'Champions League'
    }
    
    search_term = leagues.get(league.lower(), league)
    news = newsapi.get_league_news(search_term, page_size=limit)
    
    return jsonify({
        "success": True,
        "count": len(news),
        "news": news,
        "league": search_term
    })

@app.route('/api/news/team/<team>')
def get_team_news(team):
    """Get news for specific team"""
    limit = request.args.get('limit', 15, type=int)
    
    # Common team names
    teams = {
        'liverpool': 'Liverpool FC',
        'manutd': 'Manchester United',
        'manchester-united': 'Manchester United',
        'mancity': 'Manchester City',
        'manchester-city': 'Manchester City',
        'arsenal': 'Arsenal',
        'chelsea': 'Chelsea',
        'tottenham': 'Tottenham',
        'real-madrid': 'Real Madrid',
        'barcelona': 'Barcelona',
        'bayern': 'Bayern Munich',
        'juventus': 'Juventus',
        'ac-milan': 'AC Milan',
        'inter-milan': 'Inter Milan'
    }
    
    search_term = teams.get(team.lower(), team)
    news = newsapi.get_team_news(search_term, page_size=limit)
    
    return jsonify({
        "success": True,
        "count": len(news),
        "news": news,
        "team": search_term
    })

@app.route('/api/news/transfers')
def get_transfer_news():
    """Get transfer rumors and news"""
    limit = request.args.get('limit', 15, type=int)
    news = newsapi.get_transfer_news(page_size=limit)
    return jsonify({
        "success": True,
        "count": len(news),
        "news": news
    })

@app.route('/api/news/search')
def search_news():
    """Search for any football news"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify({"error": "Query too short"}), 400
    
    limit = request.args.get('limit', 15, type=int)
    news = newsapi.search_news(query, page_size=limit)
    
    return jsonify({
        "success": True,
        "query": query,
        "count": len(news),
        "news": news
    })

@app.route('/api/news/dashboard')
def news_dashboard():
    """Get complete news dashboard"""
    dashboard = newsapi.get_football_dashboard()
    return jsonify(dashboard)

@app.route('/api/news/sources')
def get_news_sources():
    """Get available sports news sources"""
    sources = newsapi.get_sports_sources()
    return jsonify({
        "success": True,
        "count": len(sources),
        "sources": sources
    })

# ==================== HELPER FUNCTION TO GET MATCH DATA ====================

def get_match_data_from_livescore(fixture_id):
    """
    Helper function to get match data from LiveScore API
    This combines data from multiple endpoints to get complete match info
    """
    try:
        # Try to get from live matches first
        live_matches = livescore.get_live_scores()
        for match in live_matches:
            if match.get('id') == fixture_id or match.get('fixture_id') == fixture_id:
                return match
        
        # If not live, try to get from fixtures
        fixtures = livescore.get_today_fixtures()
        for fixture in fixtures:
            if fixture.get('id') == fixture_id or fixture.get('fixture_id') == fixture_id:
                return fixture
        
        # If still not found, try to get match details directly
        # Note: You might need to implement this in livescore_api.py
        # For now, return a basic structure
        return {
            "id": fixture_id,
            "home_team": {"name": "Unknown"},
            "away_team": {"name": "Unknown"},
            "home_score": 0,
            "away_score": 0,
            "competition_name": "Match",
            "minute": "0",
            "events": []
        }
    except Exception as e:
        logger.error(f"Error getting match data: {e}")
        return None

# ==================== EUROPEAN COMPETITIONS ====================
EUROPEAN_COMPETITIONS = {
    # UEFA
    244: {"name": "UEFA Champions League", "country": "Europe", "flag": "🇪🇺", "tier": 1},
    245: {"name": "UEFA Europa League", "country": "Europe", "flag": "🇪🇺", "tier": 2},
    446: {"name": "UEFA Conference League", "country": "Europe", "flag": "🇪🇺", "tier": 3},
    
    # ENGLAND
    2: {"name": "Premier League", "country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "tier": 1},
    
    # SPAIN
    3: {"name": "LaLiga", "country": "Spain", "flag": "🇪🇸", "tier": 1},
    
    # GERMANY
    1: {"name": "Bundesliga", "country": "Germany", "flag": "🇩🇪", "tier": 1},
    
    # ITALY
    4: {"name": "Serie A", "country": "Italy", "flag": "🇮🇹", "tier": 1},
    
    # FRANCE
    5: {"name": "Ligue 1", "country": "France", "flag": "🇫🇷", "tier": 1},
    
    # NETHERLANDS
    196: {"name": "Eredivisie", "country": "Netherlands", "flag": "🇳🇱", "tier": 1},
    
    # PORTUGAL
    8: {"name": "Primeira Liga", "country": "Portugal", "flag": "🇵🇹", "tier": 1},
    
    # BELGIUM
    68: {"name": "Jupiler Pro League", "country": "Belgium", "flag": "🇧🇪", "tier": 1},
    
    # SCOTLAND
    75: {"name": "Scottish Premiership", "country": "Scotland", "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "tier": 1},
    
    # DENMARK
    40: {"name": "Danish Superliga", "country": "Denmark", "flag": "🇩🇰", "tier": 1},
}

# ==================== FEATURED LEAGUES ====================
FEATURED_LEAGUES = [
    {"id": 2, "name": "Premier League", "country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    {"id": 3, "name": "LaLiga", "country": "Spain", "flag": "🇪🇸"},
    {"id": 1, "name": "Bundesliga", "country": "Germany", "flag": "🇩🇪"},
    {"id": 4, "name": "Serie A", "country": "Italy", "flag": "🇮🇹"},
    {"id": 5, "name": "Ligue 1", "country": "France", "flag": "🇫🇷"},
    {"id": 75, "name": "Scottish Premiership", "country": "Scotland", "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
    {"id": 40, "name": "Danish Superliga", "country": "Denmark", "flag": "🇩🇰"},
]

# ==================== UEFA COMPETITIONS ====================
UEFA_COMPETITIONS = [
    {"id": 244, "name": "UEFA Champions League", "country": "Europe", "flag": "🇪🇺"},
    {"id": 245, "name": "UEFA Europa League", "country": "Europe", "flag": "🇪🇺"},
    {"id": 446, "name": "UEFA Conference League", "country": "Europe", "flag": "🇪🇺"},
]

# ==================== MAIN ROUTE ====================
@app.route('/')
def index():
    """Serve the main dashboard"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        return f"Template Error: {e}", 500

# ==================== API STATUS ====================
@app.route('/api/status')
def api_status():
    """Check API connection status"""
    status = livescore.test_connection()
    return jsonify(status)

# ==================== GEMINI AI ENDPOINTS ====================

@app.route('/api/gemini/status', methods=['GET'])
def gemini_status():
    """Check Gemini AI service status"""
    status = gemini.test_connection()
    return jsonify(status)

@app.route('/api/gemini/enhance', methods=['POST'])
def gemini_enhance():
    """Enhance WhatsApp message"""
    if not gemini.is_available():
        return jsonify({"error": "Gemini AI not configured", "success": False}), 503
    
    data = request.json
    message = data.get('message', '')
    tone = data.get('tone', 'exciting')
    
    if not message:
        return jsonify({"error": "No message provided", "success": False}), 400
    
    enhanced = gemini.enhance_whatsapp_message(message, tone)
    
    return jsonify({
        "success": True,
        "original": message,
        "enhanced": enhanced,
        "tone": tone
    })

@app.route('/api/gemini/translate', methods=['POST'])
def gemini_translate():
    """Translate message to another language"""
    if not gemini.is_available():
        return jsonify({"error": "Gemini AI not configured", "success": False}), 503
    
    data = request.json
    message = data.get('message', '')
    language = data.get('language', 'es')
    
    if not message:
        return jsonify({"error": "No message provided", "success": False}), 400
    
    translated = gemini.translate_message(message, language)
    
    return jsonify({
        "success": True,
        "original": message,
        "translated": translated,
        "language": language
    })

@app.route('/api/gemini/match/<int:fixture_id>/summary', methods=['GET'])
def gemini_match_summary(fixture_id):
    """Generate AI match summary"""
    if not gemini.is_available():
        return jsonify({"error": "Gemini AI not configured", "success": False}), 503
    
    # Get match data from livescore API using our helper function
    match = get_match_data_from_livescore(fixture_id)
    
    if not match:
        return jsonify({"error": "Match not found", "success": False}), 404
    
    summary = gemini.generate_match_summary(match)
    
    return jsonify({
        "success": True,
        "fixture_id": fixture_id,
        "summary": summary,
        "match": match
    })

@app.route('/api/gemini/news/summarize', methods=['POST'])
def gemini_news_summary():
    """Summarize news articles"""
    if not gemini.is_available():
        return jsonify({"error": "Gemini AI not configured", "success": False}), 503
    
    data = request.json
    articles = data.get('articles', [])
    
    if not articles:
        return jsonify({"error": "No articles provided", "success": False}), 400
    
    summary = gemini.summarize_news(articles)
    
    return jsonify({
        "success": True,
        "summary": summary,
        "article_count": len(articles[:5])
    })

@app.route('/api/gemini/enhance-batch', methods=['POST'])
def gemini_enhance_batch():
    """Enhance multiple messages at once"""
    if not gemini.is_available():
        return jsonify({"error": "Gemini AI not configured", "success": False}), 503
    
    data = request.json
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({"error": "No messages provided", "success": False}), 400
    
    enhanced = gemini.enhance_batch_messages(messages)
    
    return jsonify({
        "success": True,
        "original_count": len(messages),
        "enhanced_count": len(enhanced),
        "enhanced": enhanced
    })

# ==================== DEBUG ENDPOINTS ====================
@app.route('/api/debug/raw')
def debug_raw_scores():
    """See EXACTLY what the API returns"""
    matches = livescore.get_live_scores()
    
    if matches and len(matches) > 0:
        sample = matches[0]
        return jsonify({
            "count": len(matches),
            "sample": sample,
            "extracted_scores": {
                "home_score": sample.get('home_score', 0),
                "away_score": sample.get('away_score', 0),
                "score_display": sample.get('score_display', '')
            }
        })
    return jsonify({"error": "No matches", "count": 0})

# ==================== LIVE SCORES ====================
@app.route('/api/live')
@app.route('/api/livescores')
@app.route('/api/fixtures/live')
@app.route('/api/fixtures/live/details')
def get_live_scores():
    """Get all live matches - FIXED score mapping"""
    competition_id = request.args.get('competition_id', type=int)
    matches = livescore.get_live_scores(competition_id)
    
    formatted_matches = []
    for match in matches[:30]:
        # Get competition info
        comp_id = match.get('competition_id')
        comp_info = EUROPEAN_COMPETITIONS.get(comp_id, {})
        
        # CRITICAL FIX: Get scores directly from the API's extracted values
        home_score = match.get('home_score', 0)
        away_score = match.get('away_score', 0)
        
        # Get team names
        home_name = match.get('home_name', 'Home')
        away_name = match.get('away_name', 'Away')
        
        # Get minute
        minute = match.get('minute', '0')
        
        # Get status
        status = match.get('status', 'LIVE')
        
        formatted_matches.append({
            "id": match.get('id', match.get('fixture_id')),
            "competition_id": comp_id,
            "competition_name": comp_info.get("name", match.get('competition_name', 'Live Match')),
            "competition_flag": comp_info.get("flag", "⚽"),
            "home_team": {
                "id": match.get('home_id'),
                "name": home_name,
                "score": home_score
            },
            "away_team": {
                "id": match.get('away_id'),
                "name": away_name,
                "score": away_score
            },
            "minute": minute,
            "status": status,
            "score_display": f"{home_score} - {away_score}",
            "venue": match.get('location')
        })
    
    return jsonify(formatted_matches)

# ==================== MATCH EVENTS ====================

@app.route('/api/match/<int:fixture_id>/events')
def get_match_events_endpoint(fixture_id):
    """Get all events for a specific match with goal scorers and assists"""
    events_data = livescore.get_match_events(fixture_id)
    
    if not events_data.get('success') or not events_data.get('events'):
        return jsonify({
            "success": False,
            "error": "No events found for this match",
            "events": []
        })
    
    # Format the events for frontend display
    formatted_events = livescore.format_events_for_display(events_data['events'])
    
    # Get match info
    match_info = events_data.get('match', {})
    home_team = match_info.get('home', {})
    away_team = match_info.get('away', {})
    
    return jsonify({
        "success": True,
        "fixture_id": fixture_id,
        "match": {
            "id": fixture_id,
            "home": {
                "name": home_team.get('name'),
                "id": home_team.get('id')
            },
            "away": {
                "name": away_team.get('name'),
                "id": away_team.get('id')
            },
            "score": match_info.get('scores', {}).get('score', '0-0'),
            "status": match_info.get('status')
        },
        "events": formatted_events,
        "count": len(formatted_events)
    })

# ==================== FIXTURES ====================
@app.route('/api/fixtures/today')
def get_today_fixtures():
    """Get today's fixtures"""
    fixtures = livescore.get_today_fixtures()
    
    formatted_fixtures = []
    for fixture in fixtures[:30]:
        comp_id = fixture.get('competition_id')
        comp_info = EUROPEAN_COMPETITIONS.get(comp_id, {})
        
        formatted_fixtures.append({
            "id": fixture.get('id', fixture.get('fixture_id')),
            "competition_id": comp_id,
            "competition_name": comp_info.get("name", fixture.get('competition_name', 'Fixture')),
            "competition_flag": comp_info.get("flag", "⚽"),
            "home_team": {
                "id": fixture.get('home_id'),
                "name": fixture.get('home_name', 'Home')
            },
            "away_team": {
                "id": fixture.get('away_id'),
                "name": fixture.get('away_name', 'Away')
            },
            "date": fixture.get('date'),
            "time": fixture.get('time'),
            "venue": fixture.get('location')
        })
    
    return jsonify(formatted_fixtures)

@app.route('/api/fixtures/upcoming')
def get_upcoming_fixtures():
    """Get upcoming fixtures"""
    days = request.args.get('days', 7, type=int)
    fixtures = livescore.get_upcoming_fixtures(days)
    
    formatted_fixtures = []
    for fixture in fixtures[:50]:
        comp_id = fixture.get('competition_id')
        comp_info = EUROPEAN_COMPETITIONS.get(comp_id, {})
        
        formatted_fixtures.append({
            "id": fixture.get('id', fixture.get('fixture_id')),
            "competition_id": comp_id,
            "competition_name": comp_info.get("name", fixture.get('competition_name', 'Fixture')),
            "competition_flag": comp_info.get("flag", "⚽"),
            "home_team": {
                "id": fixture.get('home_id'),
                "name": fixture.get('home_name')
            },
            "away_team": {
                "id": fixture.get('away_id'),
                "name": fixture.get('away_name')
            },
            "date": fixture.get('date'),
            "time": fixture.get('time')
        })
    
    return jsonify(formatted_fixtures)

# ==================== STANDINGS ====================
@app.route('/api/standings/<int:competition_id>')
def get_standings(competition_id):
    """Get league standings"""
    if competition_id not in EUROPEAN_COMPETITIONS:
        return jsonify({"error": "Competition not found"}), 404
    
    comp_info = EUROPEAN_COMPETITIONS[competition_id]
    table = livescore.get_league_table(competition_id)
    
    if not table:
        return jsonify({"error": "Standings not available"}), 404
    
    formatted_standings = []
    for position, team in enumerate(table, 1):
        formatted_standings.append({
            "position": position,
            "team": {
                "id": team.get('team_id'),
                "name": team.get('name')
            },
            "played": team.get('played', 0),
            "won": team.get('won', 0),
            "drawn": team.get('drawn', 0),
            "lost": team.get('lost', 0),
            "goals_for": team.get('goals_for', 0),
            "goals_against": team.get('goals_against', 0),
            "goal_difference": team.get('goals_for', 0) - team.get('goals_against', 0),
            "points": team.get('points', 0)
        })
    
    return jsonify({
        "success": True,
        "competition": {
            "id": competition_id,
            "name": comp_info["name"],
            "country": comp_info["country"],
            "flag": comp_info["flag"]
        },
        "standings": formatted_standings
    })

# ==================== WHATSAPP FORMATTING ====================
@app.route('/api/whatsapp/standings/<int:competition_id>')
def format_standings_whatsapp(competition_id):
    """Format standings for WhatsApp"""
    if competition_id not in EUROPEAN_COMPETITIONS:
        return jsonify({"error": "Competition not found"}), 404
    
    comp_info = EUROPEAN_COMPETITIONS[competition_id]
    table = livescore.get_league_table(competition_id)
    
    if not table:
        return jsonify({"error": "Standings not available"}), 404
    
    message = f"🏆 *{comp_info['name']} TABLE* 🏆\n\n"
    message += f"📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    message += "*TOP 5*\n"
    message += "━━━━━━━━━━\n"
    
    for i, team in enumerate(table[:5], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        message += f"{medal} {team.get('name')} - *{team.get('points', 0)} pts*\n"
    
    message += f"\n#{comp_info['name'].replace(' ', '')} #Standings"
    
    return jsonify({
        "success": True,
        "message": message
    })

@app.route('/api/whatsapp/events/<int:fixture_id>')
def format_events_whatsapp(fixture_id):
    """Format match events for WhatsApp with goal scorers and assists"""
    events_data = livescore.get_match_events(fixture_id)
    
    if not events_data.get('success') or not events_data.get('events'):
        return jsonify({"error": "No events available"}), 404
    
    formatted_events = livescore.format_events_for_display(events_data['events'])
    match_info = events_data.get('match', {})
    home_team = match_info.get('home', {}).get('name', 'Home')
    away_team = match_info.get('away', {}).get('name', 'Away')
    score = match_info.get('scores', {}).get('score', '0-0')
    
    message = f"⚽ *MATCH EVENTS*\n"
    message += f"🏟️ {home_team} {score} {away_team}\n\n"
    
    for event in formatted_events:
        message += f"{event['description']}\n"
    
    message += f"\n#MatchEvents #Football"
    
    return jsonify({
        "success": True,
        "message": message
    })

# ==================== DASHBOARD ====================
@app.route('/api/dashboard')
def get_dashboard():
    """Get dashboard summary"""
    dashboard = {
        "live": {
            "count": livescore.get_live_matches_count(),
            "matches": livescore.get_live_scores()[:5]
        },
        "fixtures": {
            "today": len(livescore.get_today_fixtures()),
            "upcoming": len(livescore.get_upcoming_fixtures(3))
        },
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(dashboard)

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return render_template('index.html')

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ==================== STATIC FILES ====================
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ==================== START APP ====================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("\n" + "=" * 60)
    print("🚀 LIVESCORE API - EUROPEAN FOOTBALL DASHBOARD")
    print("=" * 60)
    
    if LIVESCORE_API_KEY and LIVESCORE_API_SECRET:
        print(f"🔑 LiveScore API Key: {LIVESCORE_API_KEY[:8]}...{LIVESCORE_API_KEY[-8:]}")
        status = livescore.test_connection()
        if status.get('key_valid'):
            print(f"✅ LiveScore Connection: SUCCESS")
            print(f"🔴 Live matches: {status.get('live_matches', 0)}")
        else:
            print(f"❌ LiveScore Connection: FAILED")
    else:
        print("❌ LiveScore API credentials missing")
    
    if GEMINI_API_KEY:
        print(f"🤖 Gemini AI Key: {GEMINI_API_KEY[:8]}...{GEMINI_API_KEY[-8:]}")
        gemini_status = gemini.test_connection()
        if gemini_status.get('available'):
            print(f"✅ Gemini AI: READY")
        else:
            print(f"❌ Gemini AI: FAILED - {gemini_status.get('message')}")
    else:
        print("❌ Gemini API key missing - AI features disabled")
    
    print("\n🌐 Server running at:")
    print(f"   • http://127.0.0.1:{port}")
    print("=" * 60 + "\n")
    
    
    
    app.run(host='0.0.0.0', port=port, debug=debug)