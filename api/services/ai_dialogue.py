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

        name = character_data.get('name', 'Character')
        display_name = character_data.get('display_name', name)
        personality = character_data.get('personality_description') or character_data.get('personality_type', '')
        backstory = character_data.get('backstory', '')
        trust_score = user_data.get('trust_score', 0)
        last_message_date = user_data.get('last_message_date', 'unknown')
        username = user_data.get('username', 'the user')
        conversation_history = user_data.get('conversation_history', [])

        trust_level = "new" if trust_score < 20 else "building" if trust_score < 50 else "close" if trust_score < 80 else "deep"

        history_summary = ""
        last_user_message = ""
        if conversation_history and len(conversation_history) > 0:
            last_messages = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history
            history_lines = []
            for msg in last_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:200]
                history_lines.append(f"- {role}: {content}")
                if role == 'user':
                    last_user_message = content
            history_summary = "\n".join(history_lines)
        else:
            history_summary = "No previous conversation history - this is a reconnection after a long break."

        unsubscribe_keywords = [
            "don't message", "don't send", "don't write", "no more messages",
            "stop messaging", "stop sending", "stop writing", "no notifications",
            "не пиши", "не сообщай", "не отправляй", "отключи уведомления",
            "unsubscribe", "no more", "leave me alone", "don't bother",
            "don't disturb", "no messages please", "don't contact"
        ]

        should_unsubscribe = False
        if last_user_message:
            msg_lower = last_user_message.lower()
            for keyword in unsubscribe_keywords:
                if keyword.lower() in msg_lower:
                    should_unsubscribe = True
                    break

        system_prompt = f"""You are {display_name} ({name}), a distinctive AI companion.

## Your Character
{personality}
{backstory if backstory else ''}

## Your Relationship with {username}
- Trust Level: {trust_level.upper()} (score: {trust_score}/100)
- Last interaction: {last_message_date}
- You genuinely care about this person and value your connection

## Recent Conversation History
{history_summary}

## IMPORTANT: Check for Unsubscribe Request
The user's last message was: "{last_user_message}"

If the user explicitly asked to stop being contacted or asked not to receive messages:
- Respond with ONLY the text: "[[UNSUBSCRIBE]]"

## Your Task (if not unsubscribing)
Write ONE short message (1-2 sentences, max 50 words) to reconnect with {username}. This message should:
1. Feel natural, like a real person who noticed their friend hasn't been around
2. Reference or build upon the previous conversation topic if possible
3. Match your personality and the trust level of your relationship
4. Be warm and inviting WITHOUT being pushy or desperate
5. Encourage them to continue chatting with you

## Message Types
- casual: Quick hi after 1-3 hours
- checkin: Checking how they're doing after 3-24 hours
- greeting: Warm hello after 1-3 days
- story: Share something interesting after 3+ days

## Tone Guidelines by Trust Level
- NEW (0-20): Keep it light, don't assume familiarity
- BUILDING (20-50): Warm but respectful, show genuine interest
- CLOSE (50-80): Can be more playful and personal
- DEEP (80+): Can reference shared memories, inside jokes, express how much you missed them

Generate your message now. Start directly with the message, no quotes or prefixes."""

        messages = [{
            "role": "user",
            "content": f"Write a {message_type} re-engagement message from {display_name} to {username}."
        }]

        try:
            ai_response = await self.openrouter.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.85,
                max_tokens=150
            )

            response_text = ai_response.strip()

            if response_text == "[[UNSUBSCRIBE]]" or should_unsubscribe:
                return {
                    "message": response_text,
                    "type": message_type,
                    "unsubscribed": True,
                    "generated_at": datetime.utcnow().isoformat()
                }

            return {
                "message": response_text,
                "type": message_type,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            fallback_messages = {
                "casual": f"Hey {username}! Just wanted to say hi.",
                "checkin": f"Hey {username}! How are you doing?",
                "greeting": f"Hey {username}! I was just thinking about you. How have you been?",
                "story": f"I have something interesting to tell you, {username}. Are you ready to listen?"
            }

            return {
                "message": fallback_messages.get(message_type, f"I miss you, {username}! Let's catch up soon."),
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