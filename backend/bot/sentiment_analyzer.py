"""
Sentiment Analysis Module
Monitors news and social sentiment for stocks
"""
import requests
from datetime import datetime, timedelta

class SentimentAnalyzer:
    def __init__(self, alpaca_headers):
        self.headers = alpaca_headers
        self.sentiment_cache = {}
        self.cache_duration = 3600  # 1 hour cache
    
    def get_news_sentiment(self, symbol):
        """Get news sentiment for a symbol using Alpaca News API"""
        # Check cache
        cache_key = f"{symbol}_{datetime.now().hour}"
        if cache_key in self.sentiment_cache:
            return self.sentiment_cache[cache_key]
        
        try:
            # Get news from Alpaca
            end = datetime.now()
            start = end - timedelta(days=1)
            
            url = 'https://data.alpaca.markets/v1beta1/news'
            params = {
                'symbols': symbol,
                'start': start.isoformat() + 'Z',
                'end': end.isoformat() + 'Z',
                'limit': 10,
                'sort': 'desc'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            
            if response.status_code != 200:
                return {'score': 0, 'articles': 0}
            
            news = response.json().get('news', [])
            
            if not news:
                return {'score': 0, 'articles': 0}
            
            # Analyze sentiment from headlines
            sentiment_score = 0
            for article in news:
                headline = article.get('headline', '').lower()
                summary = article.get('summary', '').lower()
                
                # Simple keyword-based sentiment
                positive_words = ['surge', 'rally', 'gain', 'beat', 'upgrade', 'bullish', 'strong', 'growth', 'profit', 'record']
                negative_words = ['plunge', 'drop', 'fall', 'miss', 'downgrade', 'bearish', 'weak', 'loss', 'decline', 'warning']
                
                text = headline + ' ' + summary
                
                pos_count = sum(1 for word in positive_words if word in text)
                neg_count = sum(1 for word in negative_words if word in text)
                
                if pos_count > neg_count:
                    sentiment_score += 1
                elif neg_count > pos_count:
                    sentiment_score -= 1
            
            # Normalize to -1 to 1 scale
            normalized_score = sentiment_score / len(news) if news else 0
            
            result = {
                'score': normalized_score,
                'articles': len(news)
            }
            
            # Cache result
            self.sentiment_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"Error getting sentiment for {symbol}: {e}")
            return {'score': 0, 'articles': 0}
    
    def adjust_confidence_for_sentiment(self, base_confidence, symbol):
        """Adjust confidence based on news sentiment"""
        sentiment = self.get_news_sentiment(symbol)
        
        if sentiment['articles'] == 0:
            # No news, no adjustment
            return base_confidence
        
        score = sentiment['score']
        
        # Adjust confidence based on sentiment
        if score > 0.3:
            # Very positive news
            adjustment = 10
        elif score > 0:
            # Slightly positive news
            adjustment = 5
        elif score < -0.3:
            # Very negative news - avoid
            adjustment = -25
        elif score < 0:
            # Slightly negative news
            adjustment = -10
        else:
            adjustment = 0
        
        adjusted = base_confidence + adjustment
        return max(0, min(100, adjusted))
