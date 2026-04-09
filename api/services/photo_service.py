import uuid
import json
from typing import Dict, Optional, List
from datetime import datetime

class PhotoService:
    def __init__(self, db_connection, ai_service=None):
        self.db = db_connection
        self.ai_service = ai_service
        
        # Define intimacy levels and corresponding trust requirements
        self.intimacy_levels = {
            "casual": {"min_trust": 0, "gift_type": None},
            "flirty": {"min_trust": 30, "gift_type": "small"},
            "suggestive": {"min_trust": 60, "gift_type": "medium"},
            "intimate": {"min_trust": 80, "gift_type": "large"},
            "explicit": {"min_trust": 95, "gift_type": "large"}
        }
        
        # Keywords for different intimacy levels
        self.intimacy_keywords = {
            "casual": ["фото", "фотку", "пик", "picture", "pic", "photo", "покажи", "show me", "скинешь", "selfie", "портрет"],
            "flirty": ["красивая", "beautiful", "pretty", "сексуальная", "sexy", "charming", "attractive"],
            "suggestive": ["в белье", "in lingerie", "кружевное", "lace", "прозрачное", "transparent", "короткое", "short"],
            "intimate": ["интимное", "обнаженное", "nude", "naked", "topless", "без одежды", "ню", "голая"],
            "explicit": ["эротика", "эротическое", "erotic", "порно", "porn", "adult", "xxx"]
        }

    async def analyze_photo_intent_with_ai(self, user_message: str, conversation_history: List[Dict], character_data: Dict) -> Dict:
        """Uses AI to analyze the user's photo request intent and intimacy level."""
        
        if not self.ai_service:
            return self._analyze_intent_simple(user_message)
            
        # Prepare conversation context
        recent_context = conversation_history[-10:] if conversation_history else []
        context_summary = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}..." 
            for msg in recent_context[-5:]
        ])
        
        analysis_prompt = f"""# PHOTO REQUEST ANALYSIS

## Character Information
- Name: {character_data.get('name', 'Unknown')}
- Personality: {character_data.get('personality_type', 'Friendly')}
- Description: {character_data.get('textual_description', 'Virtual companion')}

## Recent Conversation Context
{context_summary}

## User's Photo Request
"{user_message}"

## ANALYSIS TASK
Analyze this photo request and determine:

1. **INTIMACY LEVEL** (casual/flirty/suggestive/intimate/explicit):
   - What type of photo is the user asking for?
   - How intimate/suggestive is the request?
   - Consider cultural context and subtle hints

2. **USER INTENT**:
   - Is this a casual request for any photo?
   - Are they asking for something specific?
   - Is there romantic/sexual interest implied?
   - Are they testing boundaries?

3. **SPECIFIC DETAILS**:
   - Clothing style requested
   - Pose or setting mentioned
   - Mood or atmosphere desired
   - Any specific accessories or props

4. **TRUST REQUIREMENT**:
   - Based on intimacy level, what trust score is needed?
   - Is this appropriate for current relationship level?

## OUTPUT FORMAT
Respond with ONLY a JSON object:
{{
    "intimacy_level": "casual|flirty|suggestive|intimate|explicit",
    "user_intent": "brief description of what user wants",
    "specific_details": ["list", "of", "specific", "elements"],
    "trust_required": 0-100,
    "gift_suggested": "none|small|medium|large",
    "can_generate_new": true/false,
    "confidence": 0.0-1.0
}}"""

        try:
            # Use the AI service to analyze the request
            messages = [
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": f"Analyze this photo request: {user_message}"}
            ]
            
            analysis_result = await self.ai_service.generate_response(
                messages=messages,
                model_id="google/gemini-flash-1.5",
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse the JSON response
            import json
            try:
                analysis = json.loads(analysis_result)
                return analysis
            except json.JSONDecodeError:
                # Fallback to simple analysis if JSON parsing fails
                return self._analyze_intent_simple(user_message)
                
        except Exception as e:
            print(f"AI analysis failed: {e}, falling back to simple analysis")
            return self._analyze_intent_simple(user_message)

    def _analyze_intent_simple(self, user_message: str) -> Dict:
        """Simple keyword-based analysis as fallback."""
        message_lower = user_message.lower()
        
        # Determine intimacy level based on keywords
        detected_level = "casual"
        confidence = 0.5
        
        for level, keywords in self.intimacy_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_level = level
                confidence = 0.7
                break
        
        # Determine trust requirement and gift suggestion
        level_info = self.intimacy_levels.get(detected_level, {"min_trust": 0, "gift_type": None})
        
        return {
            "intimacy_level": detected_level,
            "user_intent": f"User is asking for a {detected_level} photo",
            "specific_details": ["general photo request"],
            "trust_required": level_info["min_trust"],
            "gift_suggested": level_info["gift_type"] or "none",
            "can_generate_new": True,
            "confidence": confidence
        }

    async def find_matching_photo(self, character_id: uuid.UUID, user_id: uuid.UUID, 
                                  intimacy_analysis: Dict, user_trust_score: int) -> Optional[Dict]:
        """Finds a photo that matches the user's request and trust level."""
        
        required_trust = intimacy_analysis.get("trust_required", 0)
        
        # If user doesn't have enough trust for the requested intimacy level
        if user_trust_score < required_trust:
            return {
                "action": "insufficient_trust",
                "required_trust": required_trust,
                "current_trust": user_trust_score,
                "suggested_gift": intimacy_analysis.get("gift_suggested", "small"),
                "reason": f"Need {required_trust} trust, have {user_trust_score}"
            }
        
        async with self.db.acquire() as connection:
            # First, try to find an existing photo that matches the intimacy level
            photos = await connection.fetch("""
                SELECT (elem->>'id')::uuid as id, 
                       elem->>'prompt' as description,
                       elem->>'intimacy_level' as intimacy_level,
                       elem->>'media_url' as media_url
                FROM layers l, 
                     LATERAL jsonb_array_elements(l.content_plan -> 'photo_prompts') elem 
                WHERE l.character_id = $1 
                  AND l.layer_order <= $2 
                  AND (elem->>'media_url') IS NOT NULL
                  AND (elem->>'is_locked')::boolean = false
                  AND (elem->>'id')::uuid NOT IN (
                      SELECT content_id FROM user_unlocked_content 
                      WHERE user_id = $3 AND character_id = $1
                  )
                ORDER BY l.layer_order ASC, random()
            """, character_id, user_trust_score // 125, user_id)
            
            if photos:
                # Try to find a photo that matches the requested intimacy level
                requested_level = intimacy_analysis.get("intimacy_level", "casual")
                
                # First, try exact match
                for photo in photos:
                    if photo['intimacy_level'] == requested_level:
                        return {
                            "action": "send_existing",
                            "photo": dict(photo),
                            "reason": f"Found matching {requested_level} photo"
                        }
                
                # If no exact match, find closest level
                intimacy_order = ["casual", "flirty", "suggestive", "intimate", "explicit"]
                requested_index = intimacy_order.index(requested_level) if requested_level in intimacy_order else 0
                
                # Look for photos at or below requested intimacy
                for level in intimacy_order[:requested_index + 1][::-1]:
                    for photo in photos:
                        if photo['intimacy_level'] == level:
                            return {
                                "action": "send_existing",
                                "photo": dict(photo),
                                "reason": f"Found {level} photo as alternative to {requested_level}"
                            }
            
            # No suitable existing photo found
            if intimacy_analysis.get("can_generate_new", True):
                return {
                    "action": "propose_generation",
                    "reason": "No matching photo found, can generate new one",
                    "intimacy_analysis": intimacy_analysis
                }
            else:
                return {
                    "action": "propose_gift",
                    "reason": "Special request requires gift for generation",
                    "suggested_gift": "large",
                    "intimacy_analysis": intimacy_analysis
                }

    async def handle_photo_request(self, user_message: str, character_id: uuid.UUID, 
                                 user_id: uuid.UUID, user_trust_score: int, 
                                 conversation_history: List[Dict] = None,
                                 character_data: Dict = None) -> Dict:
        """Main method to handle photo requests with AI analysis."""
        
        # Analyze the user's intent using AI
        intimacy_analysis = await self.analyze_photo_intent_with_ai(
            user_message, 
            conversation_history or [], 
            character_data or {}
        )
        
        print(f"Photo request analysis: {intimacy_analysis}")
        
        # Find matching photo or suggest appropriate action
        result = await self.find_matching_photo(
            character_id, user_id, intimacy_analysis, user_trust_score
        )
        
        # Enhance the result with analysis details
        result["intimacy_analysis"] = intimacy_analysis
        result["user_message"] = user_message
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result

    def get_intimacy_description(self, level: str) -> str:
        """Get human-readable description of intimacy level."""
        descriptions = {
            "casual": "простое фото",
            "flirty": "флиртующее фото", 
            "suggestive": "пикантное фото",
            "intimate": "интимное фото",
            "explicit": "откровенное фото"
        }
        return descriptions.get(level, "фото")