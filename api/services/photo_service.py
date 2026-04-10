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
                model_id="deepseek/deepseek-chat", # Using consistent model
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
        
        # For casual requests, explicitly mark them as general for the handler
        user_intent = f"User is asking for a {detected_level} photo"
        if detected_level == "casual":
            user_intent = f"A general, casual photo request"

        return {
            "intimacy_level": detected_level,
            "user_intent": user_intent,
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
        """Main method to handle photo requests with new, smarter logic."""
        # 1. Analyze the user's request to see if it's specific or generic
        intimacy_analysis = await self.analyze_photo_intent_with_ai(
            user_message, 
            conversation_history or [], 
            character_data or {}
        )
        
        is_generic_request = intimacy_analysis.get('intimacy_level') == 'casual' and "general" in intimacy_analysis.get('user_intent', '')

        content_match = None

        # 2. Handle the request based on its type
        if is_generic_request:
            # For generic requests, find a random piece of content the user can see now
            print("--- Generic photo request: Finding random unlockable content. ---")
            content_match = await self.find_random_unlockable_content(character_id, user_id, user_trust_score)
            if content_match:
                    response = {
                        "action": "send_existing",
                        "photo": content_match,
                        "reason": f"Found a random unlockable photo for you: {content_match['description']}"
                    }
                    print(f"[DEBUG] handle_photo_request returning for generic request: {response}")
                    return response
        else:
            # For specific requests, use AI to find the best match
            print("--- Specific photo request: Using AI to find the best match. ---")
            content_match = await self.find_best_matching_photo_with_ai(user_message, character_id, user_id)

        # 3. If a specific match was found, check trust and propose gift if needed
        if content_match and isinstance(content_match, dict):
            required_trust = content_match.get("trust_required") or 50
            if user_trust_score >= required_trust:
                return {
                    "action": "send_existing",
                    "photo": content_match,
                    "reason": f"Found a perfect match: {content_match['description']}"
                }
            else:
                return {
                    "action": "propose_gift",
                    "reason": "Found a perfect photo, but trust is too low.",
                    "suggested_gift": "medium",
                    "required_trust": required_trust,
                    "photo_description": content_match['description']
                }

        # 4. Plan C: If no content is found at all, propose generation
        print("--- No suitable content found. Using fallback message. ---")
        return {
            "action": "show_message",
            "message": "Новых фото нет."
        }
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

    async def find_best_matching_photo_with_ai(self, user_request: str, character_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Dict]:
        """Uses AI to find the best matching photo from the character's gallery."""
        async with self.db.acquire() as connection:
            # Fetch all available, locked photos for the character
            available_photos = await connection.fetch("""
                SELECT (elem->>'id')::uuid as id, 
                       elem->>'prompt' as description,
                       elem->>'intimacy_level' as intimacy_level,
                       (elem->>'trust_required')::int as trust_required
                FROM layers l, 
                     LATERAL jsonb_array_elements(l.content_plan -> 'photo_prompts') elem 
                WHERE l.character_id = $1
                  AND (elem->>'media_url') IS NOT NULL
                  AND (elem->>'id')::uuid NOT IN (
                      SELECT content_id FROM user_unlocked_content 
                      WHERE user_id = $2 AND character_id = $1
                  )
            """, character_id, user_id)

        if not available_photos:
            return None

        # Prepare the list of photos for the AI to rank
        photo_options = "\n".join([
            f"- ID: {p['id']}\n  Prompt: {p['description']}\n  Intimacy: {p['intimacy_level']}\n"
            for p in available_photos
        ])

        ranking_prompt = f"""# PHOTO MATCHING TASK

## User's Request
"{user_request}"

## Available Photos
{photo_options}

## YOUR TASK
Analyze the user's request and choose the ONE photo from the list that is the BEST possible match for the user's intent and the context. Consider the photo's prompt and intimacy level.

## OUTPUT FORMAT
Respond with ONLY the UUID of the best matching photo. For example: `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`"""

        try:
            messages = [
                {"role": "system", "content": ranking_prompt},
                {"role": "user", "content": f"Which photo is the best match for this request: '{user_request}'?"}
            ]
            
            response_text = await self.ai_service.generate_response(
                messages=messages,
                model_id="deepseek/deepseek-chat",
                temperature=0.1, # Low temperature for factual selection
                max_tokens=150 # Increased tokens in case of conversational response
            )

            # Use regex to find a UUID in the response text, making it robust
            import re
            uuid_match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', response_text, re.IGNORECASE)
            
            if not uuid_match:
                raise ValueError("No UUID found in AI response")

            best_photo_id = uuid.UUID(uuid_match.group(0))

            # Find the full photo data from the original list
            for photo in available_photos:
                if photo['id'] == best_photo_id:
                    return dict(photo)
            
            return None # Should not happen if UUID is from the list

        except Exception as e:
            print(f"AI photo matching failed: {e}, returning first available photo as fallback.")
            return dict(available_photos[0]) if available_photos else None

    async def find_random_unlockable_content(self, character_id: uuid.UUID, user_id: uuid.UUID, user_trust_score: int) -> Optional[Dict]:
        """Finds a random, not-yet-unlocked photo or teaser that the user has enough trust for."""
        async with self.db.acquire() as connection:
            content = await connection.fetchrow(
                """WITH potential_content AS (
                    SELECT elem->>'id' as id, elem->>'media_url' as url, elem->>'prompt' as description, 
                           COALESCE((elem->>'trust_required')::int, 0) as trust_required, 'photo' as type,
                           elem->>'is_locked' as is_locked
                    FROM layers l, LATERAL jsonb_array_elements(l.content_plan -> 'photo_prompts') elem
                    WHERE l.character_id = $1
                    UNION ALL
                    SELECT elem->>'id' as id, elem->>'media_url' as url, elem->>'prompt' as description, 
                           COALESCE((elem->>'trust_required')::int, 0) as trust_required, 'teaser' as type,
                           elem->>'is_locked' as is_locked
                    FROM layers l, LATERAL jsonb_array_elements(l.content_plan -> 'teaser_prompts') elem
                    WHERE l.character_id = $1
                )
                SELECT pc.id::uuid, pc.url, pc.description, pc.trust_required
                FROM potential_content pc
                WHERE pc.id IS NOT NULL
                  AND pc.url IS NOT NULL
                  AND pc.trust_required <= $2
                  AND (pc.is_locked IS NULL OR pc.is_locked = 'true')
                ORDER BY random()
                LIMIT 1;""",
                character_id, 
                user_trust_score
            )
            return dict(content) if content else None