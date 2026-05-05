"""
Chatbot Service
===============
AI-powered chatbot for customer support and book assistance.
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.logger import logger
from app.services.ai.suggestion_engine import SuggestionEngine


class ChatbotService:
    """AI-powered chatbot for user assistance."""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.intents_file = "/storage/data/chatbot/intents.json"
        self.responses_file = "/storage/data/chatbot/responses.yml"
        self.context_cache = {}
        self.intents = self._load_intents()
    
    def _load_intents(self) -> Dict[str, Any]:
        """Load chatbot intents from JSON file."""
        try:
            import json
            with open(self.intents_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load intents: {e}")
            return self._get_default_intents()
    
    def _get_default_intents(self) -> Dict[str, Any]:
        """Get default intents for fallback."""
        return {
            "greeting": {
                "patterns": ["hi", "hello", "hey", "good morning", "good evening"],
                "responses": ["Hello! How can I help you today?", "Hi there! Welcome to Abdulboy Ebook Empire!"]
            },
            "books": {
                "patterns": ["book", "books", "recommend", "suggest"],
                "responses": ["I can help you find books! What genre are you interested in?"]
            },
            "pricing": {
                "patterns": ["price", "cost", "how much", "pricing"],
                "responses": ["Books vary in price from FREE to $49.99. We also have subscription plans starting at $9.99/month."]
            },
            "subscription": {
                "patterns": ["subscribe", "subscription", "membership", "plan"],
                "responses": ["We offer Free, Basic ($9.99/mo), and Premium ($19.99/mo) plans. Premium gives you unlimited access!"]
            },
            "help": {
                "patterns": ["help", "support", "assist"],
                "responses": ["I'm here to help! You can ask me about books, pricing, subscriptions, or your account."]
            },
            "fallback": {
                "responses": ["I'm not sure I understand. Could you please rephrase?", "Let me connect you with a human agent if you need more help."]
            }
        }
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message and generate response.
        
        Args:
            message: User's message
            session_id: Chat session identifier
            user_id: Optional user ID for personalization
            
        Returns:
            Dict with response text and metadata
        """
        message = message.lower().strip()
        
        # Get conversation context
        context = self._get_context(session_id)
        
        # Detect intent
        intent = self._detect_intent(message)
        
        # Generate response based on intent
        response = await self._generate_response(intent, message, context, user_id)
        
        # Update context
        self._update_context(session_id, intent, message, response)
        
        return {
            "reply": response,
            "intent": intent,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message."""
        intents = self.intents if self.intents else self._get_default_intents()
        
        for intent_name, intent_data in intents.items():
            patterns = intent_data.get("patterns", [])
            for pattern in patterns:
                if re.search(pattern.lower(), message):
                    return intent_name
        
        return "fallback"
    
    async def _generate_response(
        self,
        intent: str,
        message: str,
        context: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Generate response based on intent and context."""
        
        if intent == "books":
            # Extract genre or query
            genres = ["fiction", "non-fiction", "mystery", "thriller", "romance", 
                      "science fiction", "fantasy", "self-help", "business"]
            
            detected_genre = None
            for genre in genres:
                if genre in message:
                    detected_genre = genre
                    break
            
            if detected_genre:
                return f"I can help you find {detected_genre} books! Would you like me to show you our top recommendations in this genre?"
            else:
                return "What genre of books are you interested in? I can recommend fiction, mystery, romance, self-help, business, and more!"
        
        elif intent == "pricing":
            if "book" in message:
                return "Book prices range from FREE for our free collection to $49.99 for premium titles. Most books are between $9.99 and $29.99."
            else:
                return "Our subscription plans: Free (limited), Basic ($9.99/month, 10 books), Premium ($19.99/month, unlimited). You save 20% with annual billing!"
        
        elif intent == "subscription":
            if "cancel" in message:
                return "You can cancel your subscription anytime from your account settings. Your access will continue until the end of your billing period."
            else:
                return "To subscribe, visit our Pricing page and choose the plan that's right for you. Premium gives you unlimited access to all books!"
        
        elif intent == "help":
            return "I can help you with: finding books, understanding pricing, managing subscriptions, or answering questions about your account. What would you like to know?"
        
        elif intent == "greeting":
            return "Hello! Welcome to Abdulboy Ebook Empire. How can I assist you today?"
        
        else:
            # Get from intents or use fallback
            intents = self.intents if self.intents else self._get_default_intents()
            responses = intents.get(intent, {}).get("responses", ["How can I help you?"])
            import random
            return random.choice(responses)
    
    def _get_context(self, session_id: str) -> Dict[str, Any]:
        """Get conversation context for session."""
        if session_id not in self.context_cache:
            self.context_cache[session_id] = {
                "history": [],
                "last_intent": None,
                "last_response": None,
                "created_at": datetime.utcnow().isoformat()
            }
        return self.context_cache[session_id]
    
    def _update_context(
        self,
        session_id: str,
        intent: str,
        message: str,
        response: str
    ) -> None:
        """Update conversation context."""
        if session_id in self.context_cache:
            self.context_cache[session_id]["history"].append({
                "user": message,
                "bot": response,
                "intent": intent,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.context_cache[session_id]["last_intent"] = intent
            self.context_cache[session_id]["last_response"] = response
            
            # Limit history size
            if len(self.context_cache[session_id]["history"]) > 20:
                self.context_cache[session_id]["history"] = self.context_cache[session_id]["history"][-20:]
    
    async def train(self, training_data: Dict[str, Any]) -> bool:
        """
        Train the chatbot with new intents and responses.
        
        Args:
            training_data: Dictionary with intents and responses
            
        Returns:
            True if training successful
        """
        try:
            # Load existing intents
            intents = self._load_intents()
            
            # Merge new intents
            for intent_name, intent_data in training_data.items():
                if intent_name in intents:
                    # Merge patterns and responses
                    intents[intent_name]["patterns"].extend(intent_data.get("patterns", []))
                    intents[intent_name]["responses"].extend(intent_data.get("responses", []))
                    # Deduplicate
                    intents[intent_name]["patterns"] = list(set(intents[intent_name]["patterns"]))
                    intents[intent_name]["responses"] = list(set(intents[intent_name]["responses"]))
                else:
                    intents[intent_name] = intent_data
            
            # Save to file
            import json
            with open(self.intents_file, 'w') as f:
                json.dump(intents, f, indent=2)
            
            self.intents = intents
            logger.info(f"Chatbot trained with {len(intents)} intents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train chatbot: {e}")
            return False
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get chatbot usage analytics."""
        total_sessions = len(self.context_cache)
        total_messages = sum(len(ctx["history"]) for ctx in self.context_cache.values())
        
        # Count intent distribution
        intent_counts = {}
        for ctx in self.context_cache.values():
            for msg in ctx["history"]:
                intent = msg.get("intent", "unknown")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return {
            "active_sessions": total_sessions,
            "total_messages": total_messages,
            "intent_distribution": intent_counts,
            "intents_loaded": len(self.intents) if self.intents else 0
        }
