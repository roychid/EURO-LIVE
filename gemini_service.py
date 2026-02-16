"""
GEMINI AI SERVICE - Google Gemini API Integration
Fixed version using official Google Generative AI library
"""

import os
import google.generativeai as genai
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-3-flash-preview"  # Using model from official docs
        self.is_available_flag = False
        
        if self.api_key:
            try:
                # Configure the Gemini client
                genai.configure(api_key=self.api_key)
                self.is_available_flag = True
                logger.info("✅ Gemini AI initialized successfully")
            except Exception as e:
                logger.error(f"❌ Gemini initialization failed: {e}")
                self.is_available_flag = False
    
    def is_available(self) -> bool:
        """Check if Gemini service is available"""
        return self.is_available_flag
    
    # ==================== MESSAGE ENHANCEMENT ====================
    
    def enhance_whatsapp_message(self, message: str, tone: str = "exciting") -> Optional[str]:
        """Enhance WhatsApp message with better formatting and emojis"""
        if not self.is_available():
            return message
        
        try:
            prompt = f"""You are a WhatsApp football content creator. Enhance this message to make it more engaging for football fans.

Original message: {message}

Tone: {tone} (exciting/professional/casual)

Rules:
- Add relevant emojis (⚽, 🏆, 🔴, ✅, etc.)
- Improve formatting with *bold* for important parts
- Keep all facts and scores exactly the same
- Make it more engaging but concise
- Max 300 characters

Enhanced message:"""
            
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini Enhancement Error: {e}")
            return message
    
    # ==================== TRANSLATION ====================
    
    def translate_message(self, message: str, target_language: str) -> Optional[str]:
        """Translate WhatsApp message to another language"""
        if not self.is_available():
            return message
        
        try:
            language_names = {
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ar': 'Arabic',
                'zh': 'Chinese',
                'ja': 'Japanese',
                'ru': 'Russian',
                'nl': 'Dutch'
            }
            
            lang_name = language_names.get(target_language, target_language)
            
            prompt = f"""Translate this football WhatsApp message to {lang_name}.

Original message: {message}

Rules:
- Keep all emojis (⚽, 🏆, 🔴, ✅, etc.)
- Keep *bold* formatting
- Keep hashtags (#Football, etc.)
- Make it sound natural in {lang_name}
- Keep football terminology accurate

Translated message:"""
            
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini Translation Error: {e}")
            return message
    
    # ==================== MATCH SUMMARIES ====================
    
    def generate_match_summary(self, match_data: Dict) -> Optional[str]:
        """Generate exciting match summary for WhatsApp"""
        if not self.is_available():
            return "Match summary unavailable - AI not configured"
        
        try:
            home = match_data.get('home_team', {})
            away = match_data.get('away_team', {})
            home_name = home.get('name', 'Home') if isinstance(home, dict) else 'Home'
            away_name = away.get('name', 'Away') if isinstance(away, dict) else 'Away'
            home_score = match_data.get('home_score', 0)
            away_score = match_data.get('away_score', 0)
            competition = match_data.get('competition_name', 'Match')
            minute = match_data.get('minute', '0')
            
            # Get events if available
            events_text = ""
            if 'events' in match_data and match_data['events']:
                events = match_data['events'][-5:]  # Last 5 events
                for event in events:
                    if isinstance(event, dict):
                        minute = event.get('minute', '')
                        player = event.get('player', 'Unknown')
                        event_type = event.get('type', '')
                        if 'GOAL' in event_type:
                            events_text += f"⚽ {minute}' - {player} scored!\n"
                        elif 'CARD' in event_type:
                            card = '🟥' if 'RED' in event_type else '🟨'
                            events_text += f"{card} {minute}' - {player} card\n"
            
            match_info = f"""
Match: {home_name} vs {away_name}
Score: {home_score} - {away_score}
Competition: {competition}
Minute: {minute}'
{events_text}
"""
            
            prompt = f"""Create an exciting WhatsApp match summary based on this data:

{match_info}

Rules:
- Start with an emoji (⚽, 🔴, ✅ based on status)
- Include current score
- Mention key moments
- Use *bold* for important parts
- Be exciting and engaging
- Max 200 characters

WhatsApp summary:"""
            
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini Match Summary Error: {e}")
            return f"⚽ {home_name} {home_score}-{away_score} {away_name}"
    
    # ==================== NEWS SUMMARIES ====================
    
    def summarize_news(self, articles: List[Dict]) -> Optional[str]:
        """Summarize football news articles into a digest"""
        if not self.is_available():
            return "News summary unavailable - AI not configured"
        
        try:
            news_text = ""
            for i, article in enumerate(articles[:5], 1):
                title = article.get('title', 'No title')
                content = article.get('content', article.get('snippet', ''))[:200]
                source = article.get('source', 'Unknown')
                news_text += f"{i}. {title}\n   {content}...\n   Source: {source}\n\n"
            
            prompt = f"""Create a WhatsApp football news digest from these articles:

{news_text}

Rules:
- Start with 📰 *FOOTBALL NEWS DIGEST*
- Summarize each article in 1 line
- Add relevant emojis
- Keep it under 300 characters total
- End with #FootballNews

WhatsApp digest:"""
            
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini News Summary Error: {e}")
            return "📰 *Football News* - Check back for updates"
    
    # ==================== BATCH ENHANCEMENT ====================
    
    def enhance_batch_messages(self, messages: List[str]) -> List[str]:
        """Enhance multiple messages at once"""
        if not self.is_available() or not messages:
            return messages
        
        try:
            enhanced_messages = []
            for message in messages:
                enhanced = self.enhance_whatsapp_message(message)
                enhanced_messages.append(enhanced)
            return enhanced_messages
            
        except Exception as e:
            logger.error(f"Gemini Batch Enhancement Error: {e}")
            return messages
    
    # ==================== TEST CONNECTION ====================
    
    def test_connection(self) -> Dict:
        """Test if Gemini API is working"""
        if not self.is_available():
            return {
                "status": "error",
                "message": "Gemini API not configured",
                "available": False
            }
        
        try:
            # Simple test prompt
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content("Say 'Football API connected' in 5 words")
            return {
                "status": "success",
                "message": response.text.strip(),
                "available": True,
                "model": self.model_name
            }
        except Exception as e:
            logger.error(f"Gemini test failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "available": False
            }