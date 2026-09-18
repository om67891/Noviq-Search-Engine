from typing import Any, Dict, Optional

def get_widget_for_query(query: str) -> Optional[Dict[str, Any]]:
    """Returns mock widget data if the query matches specific intents."""
    q = query.lower()
    
    # Weather Intent
    if "weather" in q or "temperature" in q:
        return {
            "type": "weather",
            "data": {
                "location": "New York, NY",
                "temperature": 72,
                "condition": "Sunny",
                "high": 75,
                "low": 62,
                "forecast": [
                    {"day": "Mon", "temp": 74, "icon": "☀️"},
                    {"day": "Tue", "temp": 70, "icon": "☁️"},
                    {"day": "Wed", "temp": 65, "icon": "🌧️"}
                ]
            }
        }
    
    # Finance/Stock Intent
    if "stock" in q or "price" in q or "aapl" in q or "tsla" in q:
        is_aapl = "aapl" in q or "apple" in q
        symbol = "AAPL" if is_aapl else "TSLA"
        price = 150.25 if is_aapl else 210.50
        change = 1.25 if is_aapl else -2.30
        return {
            "type": "finance",
            "data": {
                "symbol": symbol,
                "name": "Apple Inc." if is_aapl else "Tesla, Inc.",
                "price": price,
                "change": change,
                "change_percent": round(change / (price - change) * 100, 2),
                "history": [140, 142, 138, 145, 150] if is_aapl else [220, 215, 212, 208, 210]
            }
        }
        
    return None
