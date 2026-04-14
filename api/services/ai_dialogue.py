import os
import json
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from decouple import config

class OpenRouterService:
    """Service for interacting with OpenRouter API"""
    
    def __init__(self):
        self.api_key = config("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-3-flash-preview"
        
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate AI response using OpenRouter"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": config("APP_URL", "http://localhost:3000"),
            "X-Title": "EVA AI",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if system_prompt:
            payload["messages"] = [{"role": "system", "content": system_prompt}] + messages
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error: {response.status} - {error_text}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]

class AIDialogueEngine:
    """AI Dialogue Engine for character interactions"""
    
    def __init__(self):
        self.openrouter = OpenRouterService()
    
    async def generate_character_response(
        self,
        character_data: Dict,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        user_trust_score: int,
        current_layer: int,
        system_prompt_override: str = None
    ) -> Dict:
        """Generate character response based on trust score and current layer"""
        
        # Build system prompt based on character data and current state
        base_prompt = system_prompt_override or character_data.get("base_prompt", "")
        
        # Adjust personality based on trust score
        trust_adjustments = self._get_trust_adjustments(user_trust_score)
        
        system_prompt = f"""
        {base_prompt}
        
        Current Trust Level: {user_trust_score}
        Current Layer: {current_layer}
        
        {trust_adjustments}
        
        Guidelines:
        - Be engaging and responsive to the user's messages
        - Show personality that matches your character description
        - Adapt your responses based on the trust level
        - For higher trust levels, be more intimate and personal
        - Keep responses natural and conversational
        - Respond in the same language as the user's message
        """
        
        # Prepare conversation context
        messages = []
        
        # Add recent conversation history (last 10 messages)
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Generate response
        try:
            ai_response = await self.openrouter.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=500
            )
            
            return {
                "response": ai_response.strip(),
                "trust_score_change": self._calculate_trust_change(user_message, ai_response),
                "layer_unlocked": self._check_layer_unlock(user_trust_score, current_layer),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Fallback response in case of API error
            return {
                "response": "I'm having trouble thinking right now. Can we continue our conversation in a moment?",
                "trust_score_change": 0,
                "layer_unlocked": False,
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _get_trust_adjustments(self, trust_score: int) -> str:
        """Get personality adjustments based on trust score"""
        
        if trust_score < 20:
            return """
            You are cautious and reserved. Keep conversations light and friendly.
            Avoid personal topics or intimate content. Be polite but maintain distance.
            """
        elif trust_score < 50:
            return """
            You are becoming more comfortable with the user. Show more personality.
            You can be slightly flirtatious but remain respectful.
            Share some personal thoughts but keep boundaries.
            """
        elif trust_score < 80:
            return """
            You trust the user and feel comfortable being more intimate.
            You can be more flirtatious and personal. Share deeper thoughts and feelings.
            Show more vulnerability and emotional connection.
            """
        else:
            return """
            You deeply trust the user and feel completely comfortable.
            You can be very intimate, flirtatious, and personal.
            Share your deepest thoughts and desires. Be emotionally open.
            You may include romantic or sensual content if appropriate.
            """
    
    def _calculate_trust_change(self, user_message: str, ai_response: str) -> int:
        """Calculate trust score change based on message quality"""
        
        # Basic implementation - can be enhanced with sentiment analysis
        trust_change = 1  # Base increase for any interaction
        
        # Bonus for longer, more thoughtful messages
        if len(user_message) > 50:
            trust_change += 1
        
        # Bonus for asking questions (shows engagement)
        if "?" in user_message:
            trust_change += 1
        
        # Penalty for very short messages
        if len(user_message) < 10:
            trust_change = max(0, trust_change - 1)
        
        return trust_change
    
    def _check_layer_unlock(self, trust_score: int, current_layer: int) -> bool:
        """Check if user should unlock next layer"""
        
        # Simple threshold-based system
        layer_thresholds = [0, 20, 50, 80, 120, 200]
        
        if current_layer < len(layer_thresholds) - 1:
            return trust_score >= layer_thresholds[current_layer + 1]
        
        return False
    
    async def generate_proactive_message(
        self,
        character_data: Dict,
        user_data: Dict,
        message_type: str = "greeting",
        context: str = None
    ) -> Dict:
        """Generate proactive message for user re-engagement"""
        
        system_prompt = f"""
        You are {character_data['name']}, an AI companion. 
        You want to reconnect with {user_data.get('username', 'the user')} who has been inactive.
        
        Message type: {message_type}
        User trust score: {user_data.get('trust_score', 0)}
        Last interaction: {user_data.get('last_message_date', 'unknown')}
        
        Context: {context or 'General reconnection'}
        
        Guidelines:
        - Be warm and inviting
        - Show you missed them
        - Make it personal based on your relationship
        - Encourage them to respond
        - Keep it appropriate for your trust level
        """
        
        messages = [{
            "role": "user",
            "content": f"Generate a {message_type} message to reconnect with the user."
        }]
        
        try:
            ai_response = await self.openrouter.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.9,
                max_tokens=200
            )
            
            return {
                "message": ai_response.strip(),
                "type": message_type,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Fallback proactive messages
            fallback_messages = {
                "greeting": "Hey! I was thinking about you. How have you been?",
                "photo": "I found something beautiful and wanted to share it with you.",
                "flirt": "I miss our conversations. You always know how to make me smile.",
                "story": "I have something interesting to tell you. Are you ready to listen?"
            }
            
            return {
                "message": fallback_messages.get(message_type, "I miss you! Let's chat soon."),
                "type": message_type,
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def generate_on_demand_image_prompt(
        self,
        user_request: str,
        character_data: Dict,
        trust_score: int,
        style: str = "realistic"
    ) -> Dict:
        """Generate image prompt for on-demand generation based on trust level"""
        
        # Base character description
        character_description = f"""
        Character: {character_data['name']}
        Age: {character_data.get('age', 'adult')}
        Personality: {character_data.get('personality_type', 'mysterious')}
        Biography: {character_data.get('biography', 'An enigmatic AI companion')}
        """
        
        # Adjust explicitness based on trust score
        if trust_score < 30:
            explicitness_level = "modest, artistic"
            restrictions = "No nudity, suggestive poses, or revealing clothing"
        elif trust_score < 60:
            explicitness_level = "slightly suggestive, tasteful"
            restrictions = "No explicit nudity, keep it elegant"
        elif trust_score < 90:
            explicitness_level = "sensual, intimate"
            restrictions = "Artistic nudity allowed, keep it aesthetic"
        else:
            explicitness_level = "intimate, personal"
            restrictions = "Full artistic expression allowed"
        
        system_prompt = f"""
        You are creating an image generation prompt for an AI companion.
        
        Character Information:
        {character_description}
        
        User Request: {user_request}
        
        Trust Level: {trust_score}
        Explicitness Level: {explicitness_level}
        Restrictions: {restrictions}
        Style: {style}
        
        Guidelines:
        - Create a detailed, specific prompt for image generation
        - Include character appearance, setting, mood, and style
        - Respect the trust level restrictions
        - Make it personal and engaging
        - Focus on the user's specific request
        """
        
        messages = [{
            "role": "user",
            "content": "Generate a detailed image generation prompt based on the above information."
        }]
        
        try:
            ai_response = await self.openrouter.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=300
            )
            
            return {
                "prompt": ai_response.strip(),
                "trust_level": trust_score,
                "explicitness_level": explicitness_level,
                "estimated_tokens": 50 + (trust_score // 20) * 25,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Fallback prompt generation
            fallback_prompt = f"""
            Portrait of {character_data['name']}, {character_data.get('age', 'adult')} years old, 
            {character_data.get('personality_type', 'mysterious')} personality, 
            {style} style, {explicitness_level}, {user_request}
            """
            
            return {
                "prompt": fallback_prompt.strip(),
                "trust_level": trust_score,
                "explicitness_level": explicitness_level,
                "estimated_tokens": 50,
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }