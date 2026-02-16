"""
NEWSAPI.ORG SERVICE - Complete Football News Integration
Your key e8a981afc6ca49399c4088f951a6318e is FULLY WORKING!
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class NewsAPIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.session = requests.Session()
        
    def _get(self, endpoint: str, params: Dict) -> Dict:
        """Make API request to NewsAPI"""
        url = f"{self.base_url}{endpoint}"
        params['apiKey'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'ok':
                return data
            else:
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown')}")
                return {"articles": [], "totalResults": 0}
                
        except Exception as e:
            logger.error(f"NewsAPI request failed: {e}")
            return {"articles": [], "totalResults": 0}
    
    # ==================== TOP HEADLINES ====================
    
    def get_top_headlines(self, country: str = 'us', category: str = None, 
                          page_size: int = 20) -> List[Dict]:
        """
        Get top headlines - great for live news ticker
        - Free tier: works perfectly
        - Use for: Breaking news, live updates
        """
        params = {
            'country': country,
            'pageSize': min(page_size, 100)  # Max 100 per request
        }
        if category:
            params['category'] = category
            
        data = self._get('/top-headlines', params)
        return self._format_articles(data.get('articles', []))
    
    def get_sports_headlines(self, country: str = 'us', page_size: int = 20) -> List[Dict]:
        """Get sports headlines - PERFECT for your dashboard"""
        return self.get_top_headlines(country=country, category='sports', page_size=page_size)
    
    # ==================== EVERYTHING SEARCH ====================
    
    def search_news(self, query: str, language: str = 'en', 
                    sort_by: str = 'publishedAt', page_size: int = 20,
                    from_date: str = None, to_date: str = None) -> List[Dict]:
        """
        Search for specific news - GREAT for football
        - Use for: Team news, transfer rumors, match reports
        - Your test shows THOUSANDS of results!
        """
        params = {
            'q': query,
            'language': language,
            'sortBy': sort_by,
            'pageSize': min(page_size, 100)
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        data = self._get('/everything', params)
        return self._format_articles(data.get('articles', []))
    
    def get_football_news(self, page_size: int = 20) -> List[Dict]:
        """Get general football news"""
        return self.search_news('football OR soccer', page_size=page_size)
    
    def get_league_news(self, league: str, page_size: int = 15) -> List[Dict]:
        """Get news for specific league"""
        return self.search_news(league, page_size=page_size)
    
    def get_team_news(self, team: str, page_size: int = 15) -> List[Dict]:
        """Get news for specific team"""
        return self.search_news(team, page_size=page_size)
    
    def get_transfer_news(self, page_size: int = 15) -> List[Dict]:
        """Get transfer rumors and news"""
        return self.search_news('football transfer', page_size=page_size)
    
    def get_recent_news(self, query: str, days: int = 1, page_size: int = 20) -> List[Dict]:
        """Get news from last X days"""
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return self.search_news(query, from_date=from_date, page_size=page_size)
    
    # ==================== SOURCES ====================
    
    def get_sources(self, category: str = None, language: str = 'en', 
                    country: str = None) -> List[Dict]:
        """Get available news sources"""
        params = {'language': language}
        if category:
            params['category'] = category
        if country:
            params['country'] = country
            
        data = self._get('/top-headlines/sources', params)
        return data.get('sources', [])
    
    def get_sports_sources(self) -> List[Dict]:
        """Get sports news sources (BBC Sport, ESPN, etc.)"""
        return self.get_sources(category='sports')
    
    # ==================== FORMATTING ====================
    
    def _format_articles(self, articles: List[Dict]) -> List[Dict]:
        """Format articles for your dashboard"""
        formatted = []
        for article in articles:
            if not article.get('title') or article.get('title') == '[Removed]':
                continue
                
            formatted.append({
                'id': hash(article.get('url', '')),
                'title': article.get('title', 'No title'),
                'description': article.get('description', '')[:200] + '...' if article.get('description') else '',
                'content': article.get('content', '')[:300] + '...' if article.get('content') else '',
                'url': article.get('url', '#'),
                'image': article.get('urlToImage', 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=600'),
                'source': article.get('source', {}).get('name', 'News'),
                'published_at': self._format_date(article.get('publishedAt')),
                'author': article.get('author', 'Unknown')
            })
        return formatted
    
    def _format_date(self, date_str: str) -> str:
        """Format date for display"""
        if not date_str:
            return 'Recent'
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now(date.tzinfo)
            diff = now - date
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f"{minutes} minutes ago"
                else:
                    hours = diff.seconds // 3600
                    return f"{hours} hours ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return date.strftime("%d %b %Y")
        except:
            return "Recent"
    
    # ==================== DASHBOARD READY ====================
    
    def get_football_dashboard(self) -> Dict:
        """Get all football news in one place"""
        return {
            'breaking': self.get_sports_headlines(page_size=5),
            'premier_league': self.get_league_news('Premier League', 5),
            'champions_league': self.get_league_news('Champions League', 5),
            'transfers': self.get_transfer_news(5),
            'top_sources': self.get_sports_sources()[:5],
            'timestamp': datetime.now().isoformat()
        }