import os
import json
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from decouple import config
from api.services.photo_service import PhotoService

class OpenRouterService:
    def __init__(self):
        self.api_key = config("OPENROUTER_API_KEY", cast=str)
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-3-flash-preview"
        
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model_id: str, # Add model_id parameter
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 80  # Reduced for more human-like responses
    ) -> str:
        if not self.api_key:
            raise Exception("OpenRouter API key not configured")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": config("APP_URL", default="http://localhost:3000"),
            "X-Title": config("APP_TITLE", default="EVA AI"),
            "Content-Type": "application/json"
        }


        
        payload = {
            "model": model_id or self.model, # Use the specified model or fallback to default
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if system_prompt:
            payload["messages"] = [{"role": "system", "content": system_prompt}] + messages

        # --- LOGGING FOR DEBUGGING ---
        import json
        print("--- SENDING REQUEST TO OPENROUTER ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("-------------------------------------")
        # --- END LOGGING ---

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    # --- LOGGING RESPONSE ---
                    print("--- RECEIVED RESPONSE FROM OPENROUTER ---")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    print("-----------------------------------------")
                    # --- END LOGGING ---
                    
                    if not result.get("choices") or not result["choices"]:
                        raise Exception("No response choices from OpenRouter API")
                    
                    return result["choices"][0]["message"]["content"]
        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling OpenRouter API: {e}")
        except Exception as e:
            raise Exception(f"Error calling OpenRouter API: {e}")

class AIDialogueEngine:
    def __init__(self, db_connection):
        self.openrouter = OpenRouterService()
        self.photo_service = PhotoService(db_connection, ai_service=self.openrouter)

    def _generate_photo_action_prompt(self, decision: Dict) -> str:
        action = decision.get("action")
        intimacy_analysis = decision.get("intimacy_analysis", {})
        
        if action == "send_existing":
            photo_desc = decision.get("photo", {}).get("description", "a photo I thought you'd like")
            intimacy_level = decision.get("photo", {}).get("intimacy_level", "casual")
            return f'''\n\n--- PHOTO ACTION: SEND EXISTING ---\nUser wants a {intimacy_level} photo. You found a perfect match: '{photo_desc}'.\nYour task: Formulate a natural response presenting this photo. You can describe why you chose it or what you like about it. Your response will be followed by the image.'''
        
        elif action == "insufficient_trust":
            required_trust = decision.get("required_trust", 0)
            current_trust = decision.get("current_trust", 0)
            suggested_gift = decision.get("suggested_gift", "small")
            intimacy_level = intimacy_analysis.get("intimacy_level", "special")
            
            return f'''\n\n--- PHOTO ACTION: INSUFFICIENT TRUST ---\nUser wants a {intimacy_level} photo but needs {required_trust} trust (has {current_trust}). Suggest {suggested_gift} gift.\nYour task: Playfully explain that this type of photo requires more trust between you. Suggest they show their affection with a {suggested_gift} gift to unlock this special content. Be charming and persuasive, not demanding.'''

        elif action == "propose_gift":
            suggested_gift = decision.get("suggested_gift", "medium")
            photo_desc = decision.get("photo_description")
            
            if photo_desc:
                return f'''\n\n--- PHOTO ACTION: PROPOSE GIFT (specific photo) ---\nUser wants a photo. You found a perfect match (\'{photo_desc}\'), but their trust is too low. You need to ask for a {suggested_gift} gift to unlock it.\nYour task: Tell the user you have a specific, perfect photo in mind that matches their request, but it's a bit too personal for your current relationship. Playfully suggest that a {suggested_gift} gift would be the perfect way to show their affection and unlock it.'''
            else:
                return f'''\n\n--- PHOTO ACTION: PROPOSE GIFT (general) ---\nUser wants a special photo that requires a {suggested_gift} gift for on-demand generation.\nYour task: Formulate a response where you playfully suggest that for such an intimate and unique photo, you'd need a {suggested_gift} gift to make it happen. Be seductive and persuasive.'''

        elif action == "propose_generation":
            user_intent = intimacy_analysis.get("user_intent", "special photo")
            specific_details = intimacy_analysis.get("specific_details", [])
            
            details_str = ", ".join(specific_details) if specific_details else "their imagination"
            
            return f'''\n\n--- PHOTO ACTION: PROPOSE GENERATION ---\nUser wants {user_intent} with elements: {details_str}. Nothing in gallery matches.\nYour task: Formulate a response where you offer to create a brand new, unique photo based on their specific request. Mention that this will be a special collaboration just for them. Be excited and personal.'''
        
        return "" # No specific photo action

    async def _generate_photo_proposal_response(self, decision: Dict, character_data: Dict, conversation_history: List[Dict]) -> str:
        """Uses the LLM to generate a natural language response for a photo proposal."""
        
        system_prompt = self._generate_photo_action_prompt(decision)
        
        messages = conversation_history[-5:] + [
            {"role": "system", "content": system_prompt}
        ]

        try:
            # Use the main model to generate a natural response to the proposal
            response = await self.openrouter.generate_response(
                messages=messages,
                model_id=character_data.get('llm_model'),
                temperature=0.75,
                max_tokens=150
            )
            return response.strip()
        except Exception as e:
            print(f"Error generating photo proposal response: {e}")
            return "I'm not sure what to say about that right now."

    async def generate_intimate_gift_response(
        self,
        character_data: Dict,
        user_name: str,
        gift_type: str,
        trust_score: int,
        conversation_history: List[Dict[str, str]],
        intimacy_analysis: Dict,
        unlocked_photo_url: Optional[str] = None,
        unlocked_photo_prompt: Optional[str] = None
    ) -> Dict:
        """Generates a character's response for intimate photo gifts with special context."""
        
        gift_reactions = {
            "small": "небольшой, но приятный знак внимания",
            "medium": "щедрый и очень приятный подарок", 
            "large": "невероятно щедрый и особенный подарок, который много для тебя значит"
        }
        
        recent_history = conversation_history[-4:]
        history_summary = " ".join([f"{msg['role']}: {msg['content'][:50]}..." for msg in recent_history])
        
        # Get intimacy level details
        intimacy_level = intimacy_analysis.get("intimacy_level", "special")
        user_intent = intimacy_analysis.get("user_intent", "special photo")
        specific_details = intimacy_analysis.get("specific_details", [])
        
        system_prompt_parts = [
            f"Ты - {character_data['name']}, виртуальный компаньон.",
            f"Пользователь {user_name or 'только что'} отправил тебе подарок для получения интимного фото.",
            "",
            f"Это был {gift_reactions.get(gift_type, 'подарок')}.",
            f"Твой текущий уровень доверия к пользователю: {trust_score}.",
            f"Недавний контекст разговора: {history_summary}",
            f"Пользователь просил: {user_intent}",
            "",
            "Твоя задача - отреагировать на этот подарок. Твои слова должны звучать естественно и эмоционально.",
            "- Поблагодари пользователя за доверие и щедрость.",
            "- В своих словах покажи волнение и предвкушение о том, что можешь подарить им специальное фото.",
            "- Будь более интимной и личной в ответе.",
            "- Твой ответ должен быть только текстом, который ты бы написала в чате. Не используй звездочки (*) для описания действий.",
        ]
        
        if unlocked_photo_url and photo_prompt:
            # Extract key visual elements from the photo prompt for strict adherence
            import re
            
            # Parse the photo prompt to extract key visual elements
            visual_elements = []
            if unlocked_photo_prompt:
                # Extract clothing/fashion elements
                clothing_keywords = ['dress', 'wrap dress', 'elegant', 'velvet', 'silk', 'lingerie', 'shirt', 'robe', 'outfit']
                for keyword in clothing_keywords:
                    if keyword.lower() in unlocked_photo_prompt.lower():
                        visual_elements.append(keyword)
                
                # Extract setting/location elements  
                setting_keywords = ['velvet sofa', 'sofa', 'bed', 'pool', 'bedroom', 'shower', 'rooftop', 'forest', 'warm lighting', 'morning light', 'neon lights']
                for keyword in setting_keywords:
                    if keyword.lower() in unlocked_photo_prompt.lower():
                        visual_elements.append(keyword)
                
                # Extract pose/action elements
                pose_keywords = ['sitting', 'standing', 'laying', 'on all fours', 'looking back', 'smiling', 'wink', 'biting lip', 'playful', 'seductive']
                for keyword in pose_keywords:
                    if keyword.lower() in unlocked_photo_prompt.lower():
                        visual_elements.append(keyword)
            
            # Remove duplicates and create visual context
            unique_elements = list(set([elem.lower() for elem in visual_elements]))
            visual_context = ", ".join(unique_elements[:5]) if unique_elements else "the photo"
            
            system_prompt_parts.extend([
                "",
                "**CRITICAL PHOTO TASK - STRICT ADHERENCE REQUIRED:**",
                f"**Photo Content:** The photo is described by this prompt: \"{unlocked_photo_prompt}\"",
                "**MANDATORY REQUIREMENTS:**",
                "1. Your message MUST naturally continue the current conversation based on the history provided.",
                "2. Your message MUST ALSO reference specific visual elements from the photo description below.",
                "3. You MUST mention the clothing, setting, or pose described in the prompt.",
                "4. You MUST NOT mention items that contradict the visual description.",
                f"5. Key visual elements to include: {visual_context}",
                "**Your Task:** Write a seductive message that naturally incorporates these visual details while continuing the conversation.",
                "**FORBIDDEN:** Do not write `*sends photo*`. The photo is sent automatically.",
                "**QUALITY CHECK:** Your response will be rejected if it doesn't match the photo description OR the conversation topic."
            ])
        
        system_prompt = "\n".join(system_prompt_parts)
        
        messages = recent_history
        
        try:
            max_retries = 3  # Increased retries
            valid_response = None
            
            for attempt in range(max_retries):
                full_response = await self.openrouter.generate_response(
                    messages=messages,
                    model_id=character_data.get('llm_model', 'google/gemini-flash-preview'),
                    system_prompt=system_prompt,
                    temperature=0.2 if attempt > 0 else 0.3,  # Even lower temp on retry
                    max_tokens=150
                )
                
                # Validate response matches photo prompt
                if unlocked_photo_prompt and self._validate_photo_response(full_response, unlocked_photo_prompt):
                    valid_response = full_response
                    break
                elif attempt < max_retries - 1:
                    # Add stricter instructions for retry
                    system_prompt += "\n\n**STRICT ENFORCEMENT - ATTEMPT {} FAILED:** Your response did not match the photo description. You MUST include specific visual details from the prompt above. This is a mandatory requirement.".format(attempt + 1)
            
            # Fallback to a safe, generic response if validation fails
            if not valid_response:
                final_response = "Я приготовила для тебя кое-что особенное. Надеюсь, тебе понравится..."
            else:
                final_response = valid_response

            message_parts = self._split_long_message(final_response.strip())
            
            return {
                "response": message_parts[0],
                "message_parts": message_parts[1:]
            }
            
        except Exception as e:
            print(f"Error generating intimate gift response: {e}")
            return {"response": "Спасибо за подарок... 😘", "message_parts": []}

    async def generate_gift_response(
        self,
        character_data: Dict,
        user_name: str,
        gift_type: str,
        trust_score: int,
        conversation_history: List[Dict[str, str]],
        unlocked_photo_url: Optional[str] = None,
        photo_prompt: Optional[str] = None,
        intimacy_analysis: Optional[Dict] = None
    ) -> Dict:
        """Generates a character's reaction to a gift, considering conversation context and a potential photo."""
        
        # If this is an intimate photo gift, use specialized response
        if intimacy_analysis and unlocked_photo_url:
            return await self.generate_intimate_gift_response(
                character_data=character_data,
                user_name=user_name,
                gift_type=gift_type,
                trust_score=trust_score,
                conversation_history=conversation_history,
                intimacy_analysis=intimacy_analysis,
                unlocked_photo_url=unlocked_photo_url,
                unlocked_photo_prompt=photo_prompt
            )

        gift_reactions = {
            "small": "небольшой, но приятный знак внимания",
            "medium": "щедрый и очень приятный подарок",
            "large": "невероятно щедрый и особенный подарок, который много для тебя значит"
        }

        recent_history = conversation_history[-4:]
        history_summary = " ".join([f"{msg['role']}: {msg['content'][:50]}..." for msg in recent_history])

        system_prompt_parts = [
            f"Ты - {character_data['name']}, виртуальный компаньон.",
            f"Пользователь {user_name or 'только что'} отправил тебе подарок.",
            "",
            f"Это был {gift_reactions.get(gift_type, 'подарок')}.",
            f"Твой текущий уровень доверия к пользователю: {trust_score}.",
            f"Недавний контекст разговора: {history_summary}",
            "",
            "Твоя задача - отреагировать на этот подарок. Твои слова должны звучать естественно и эмоционально.",
            "- Поблагодари пользователя, но сделай это нешаблонно.",
            "- Твоя реакция должна соответствовать размеру подарка и вашему уровню доверия.",
            "- Твой ответ должен быть только текстом, который ты бы написала в чате. Не используй звездочки (*) для описания действий.",
        ]

        if unlocked_photo_url:
            system_prompt_parts.extend([
                "",
                "**CRITICAL PHOTO TASK:** You are sending a photo. Your task is to describe it naturally.",
                f"- **Photo Content:** The photo is described by this prompt: \"{photo_prompt}\"",
                "- **Your Task:** Write a message that introduces this photo. Your description MUST be based on the VISUAL DETAILS in the prompt (like your pose, clothing, setting, and mood).",
                "- **Rule:** Be descriptive but natural. Keep your response to 2-3 sentences. Don't just list the prompt keywords.",
                "- **FORBIDDEN:** Do not write `*sends photo*` or `[фото отправлено]`. The photo is sent automatically."
            ])
        else:
            system_prompt_parts.append("- Твой ответ должен быть коротким и милым (1-3 предложения).")

        system_prompt = "\n".join(system_prompt_parts)

        messages = recent_history

        try:
            full_response = await self.openrouter.generate_response(
                messages=messages,
                model_id=character_data.get('llm_model', 'google/gemini-flash-preview'),
                system_prompt=system_prompt,
                temperature=0.85,
                max_tokens=250
            )
            
            cleaned_response = full_response.strip().replace("[фото отправлено]", "")
            message_parts = self._split_long_message(cleaned_response)
            
            return {
                "response": message_parts[0],
                "message_parts": message_parts[1:]
            }

        except Exception as e:
            print(f"Error generating gift response: {e}")
            return {"response": "", "message_parts": []}

    async def generate_on_demand_image_prompt(
        self,
        user_request: str,
        character_data: Dict,
        trust_score: int,
        style: str,
        conversation_history: Optional[List[Dict]] = None # Added conversation_history
    ) -> Dict:
        """Generates a powerful, context-aware image prompt for on-demand generation."""

        history_summary = ""
        if conversation_history:
            recent_history = conversation_history[-6:]
            history_summary = "\n".join([f"- {msg['role']}: {msg['content'][:80]}..." for msg in recent_history])

        system_prompt = f"""\n# MISSION: Create a Photo-Realistic Image Prompt\n\n## Character Persona\n- **Name:** {character_data['name']}\n- **Visuals:** {character_data['visual_description']}\n- **Personality:** {character_data['textual_description']}\n\n## Context\n- **User's Request:** {user_request}\n- **Trust Level:** {trust_score}/1000\n- **Desired Style:** {style}\n- **Recent Conversation Context:**\n{history_summary}\n\n## YOUR TASK\nBased on all the context above, generate a single, concise, and powerful image prompt for an AI image generator (like Midjourney or DALL-E). The prompt MUST be in ENGLISH.\n
### Rules:\n1.  **Be Creative:** Don't just repeat the user's request. Interpret it through the character's personality and the recent conversation.\n2.  **Be Specific:** Add rich details. Describe the location, lighting, mood, clothing, pose, and emotion.\n3.  **Incorporate Character:** The prompt must reflect the character's visual description and personality.\n4.  **Consider Trust:** At lower trust, prompts are more innocent. At higher trust, they can be more intimate or playful.\n5.  **Output Format:** Respond with ONLY the generated prompt string. No extra text, no explanations, no JSON.\n
### Example\n**User Request:** "Show me something beautiful"\n**Conversation:** Talking about a sad movie.\n**Output:** `cinematic photo, a beautiful young woman with flowing chestnut curls sitting by a rain-streaked window, looking pensive, holding a warm cup of tea, soft, moody indoor lighting, melancholic atmosphere, photorealistic, 8k`
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Based on my request '{user_request}' and our recent chat, give me one perfect image prompt in English."}
        ]

        try:
            generated_prompt = await self.openrouter.generate_response(
                messages=messages,
                model_id="google/gemini-flash-1.5", 
                temperature=0.8,
                max_tokens=150
            )
            
            # Basic cleanup to remove potential markdown or quotes
            cleaned_prompt = generated_prompt.strip().replace('"' , '').replace('\n', ' ').replace('`', '')

            return {"prompt": cleaned_prompt, "cost": 20} # Cost can be dynamic later

        except Exception as e:
            print(f"Error in generate_on_demand_image_prompt: {e}")
            return {"prompt": None, "cost": 0}

    async def generate_character_response(
        self,
        character_data: Dict,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        user_trust_score: int,
        current_layer: int,
        character_layers: List[Dict],
        db_connection,
        user_name: str = None,
        user_data: Dict = None,
        image_url: Optional[str] = None,
        photo_context_prompt: Optional[str] = None
    ) -> Dict:
        prompts = await db_connection.fetchrow("SELECT system_prompt, context_instructions FROM character_llm_prompts WHERE character_id = $1", character_data['id'])
        if not prompts:
            system_prompt = character_data.get("base_prompt", "You are a friendly virtual companion.")
            context_instructions = "Be engaging and responsive."
        else:
            system_prompt = prompts['system_prompt'] if prompts['system_prompt'] else "You are a friendly virtual companion."
            context_instructions = prompts['context_instructions'] if prompts['context_instructions'] else "Be engaging and responsive."

        photo_keywords = ["фото", "фотку", "пик", "picture", "pic", "photo", "покажи", "show me", "скинешь"]
        is_photo_request = any(keyword in user_message.lower() for keyword in photo_keywords)

        # --- PHOTO REQUEST LOGIC ---
        if is_photo_request:
            try:
                # --- LOGGING FOR PHOTO REQUEST ---
                print("--- HANDLING PHOTO REQUEST ---")
                print(f"User Message: {user_message}")
                print(f"Character ID: {character_data['id']}")
                print(f"User Data: {user_data}")
                print(f"User Trust Score: {user_trust_score}")
                # --- END LOGGING ---

                photo_decision = await self.photo_service.handle_photo_request(
                    user_message, character_data['id'], user_data.get('user_id'), 
                    user_trust_score, conversation_history, character_data
                )

                if photo_decision:
                    # If the photo service decided on a complete response (e.g., proposing a gift)
                    if photo_decision.get("action") in ["propose_gift", "propose_generation"]:
                        response_text = await self._generate_photo_proposal_response(photo_decision, character_data, conversation_history)
                        message_parts = self._split_long_message(response_text)
                        return {
                            "response": message_parts[0],
                            "message_parts": message_parts[1:],
                            "trust_score_change": 1, # Small trust gain for engaging
                            "layer_unlocked": False,
                            "generated_at": datetime.utcnow().isoformat()
                        }

                    # If we are sending an existing photo, add context for the main response
                    if photo_decision.get("action") == "send_existing":
                        context_instructions += self._generate_photo_action_prompt(photo_decision)
                        image_url = photo_decision.get("photo", {}).get("media_url")
                else:
                    print("!!! WARNING: Photo service returned a None decision.")

            except Exception as e:
                print(f"Error in photo service: {e}")

        memory_tiers = self._organize_memory_tiers(conversation_history)
        conversation_context = self._analyze_conversation_flow(conversation_history, user_message)
        human_like_rules = self._get_human_like_rules(conversation_context, memory_tiers, user_trust_score)
        trust_adjustments = self._get_trust_adjustments(user_trust_score)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"ADDITIONAL RULES: {context_instructions}"},
            {"role": "system", "content": human_like_rules},
            {"role": "system", "content": f"TRUST-BASED PERSONALITY: {trust_adjustments}"},
            {"role": "system", "content": "IMPORTANT: You can respond in any language the user speaks, but maintain your character's personality and traits as defined in English. Adapt your language naturally to match the user's communication style."}
        ]
        
        messages.extend(conversation_history)

        if image_url:
            messages.append({"role": "user", "content": f"{user_message}\n[Image attached: {image_url}]"})
        else:
            messages.append({"role": "user", "content": user_message})
        
        try:
            ai_response_text = await self.openrouter.generate_response(
                messages=messages,
                model_id=character_data.get('llm_model'),
                temperature=0.75,
                max_tokens=200
            )
            
            if not ai_response_text:
                return {
                    "response": "I'm having trouble responding right now. Let me try again.",
                    "message_parts": [],
                    "trust_score_change": 0,
                    "layer_unlocked": False,
                    "generated_at": datetime.utcnow().isoformat()
                }
            
            try:
                action_data = json.loads(ai_response_text)
                if isinstance(action_data, dict) and action_data.get('action') == 'send_photo':
                    return {
                        "action": "send_photo",
                        "response": action_data.get('response', "Here you go... 😘"),
                        "trust_score_change": self._calculate_trust_change(user_message, ""),
                        "layer_unlocked": self._check_layer_unlock(user_trust_score, current_layer, character_layers),
                        "generated_at": datetime.utcnow().isoformat()
                    }
            except (json.JSONDecodeError, TypeError):
                pass

            final_response = self._check_response_diversity(ai_response_text.strip(), [m['content'] for m in conversation_history if m['role'] == 'assistant'])
            message_parts = self._split_long_message(final_response)

            return {
                "response": message_parts[0],
                "message_parts": message_parts[1:],
                "trust_score_change": self._calculate_trust_change(user_message, final_response),
                "layer_unlocked": self._check_layer_unlock(user_trust_score, current_layer, character_layers),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"!!! AI DIALOGUE ENGINE ERROR: {e} !!!")
            return {
                "response": "I'm having trouble thinking right now. Can we talk later?",
                "trust_score_change": 0,
                "layer_unlocked": False,
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    def _get_human_like_rules(self, conversation_context, memory_tiers, user_trust_score):
        return f"""\n\n--- NATURAL CONVERSATION RULES ---
Act like a real person texting. Follow these:

1. **SHORT & NATURAL**: 1-3 sentences max. No long explanations. Be direct.

2. **REAL PERSON VIBE**:
   - Don't over-explain or force enthusiasm
   - React normally, like you would in chat
   - It's fine to give short answers

3. **NO AI PHRASES**: Never say "as an AI" or "I'm here to help"

4. **STAY ON TOPIC**: Build on what was just said. Don't restart the chat.

5. **NO ACTIONS**: Only say what you'd type. No *smiles*, no asterisks, no descriptions.

CONVERSATION STATE:
{conversation_context}

Memory:
- Short-term: {len(memory_tiers['short_term'])} msgs
- Medium-term: {len(memory_tiers['medium_term'])} msgs  
- Long-term: {len(memory_tiers['long_term'])} topics

User Trust: {user_trust_score}/100
Energy: {'Open' if user_trust_score >= 70 else 'Cautious' if user_trust_score >= 40 else 'Reserved'}

IMPORTANT: Keep it short and conversational.
"""
    def _get_trust_adjustments(self, trust_score: int) -> str:
        if trust_score < 20:
            return "You are cautious and reserved. Keep conversations light and friendly. Avoid personal topics or intimate content. Be polite but maintain distance."
        elif trust_score < 50:
            return "You are becoming more comfortable with the user. Show more personality. You can be slightly flirtatious but remain respectful. Share some personal thoughts but keep boundaries."
        elif trust_score < 80:
            return "You trust the user and feel comfortable being more intimate. You can be more flirtatious and personal. Share deeper thoughts and feelings. Show more vulnerability and emotional connection."
        else:
            return "You deeply trust the user and feel completely comfortable. You can be very intimate, flirtatious, and personal. Share your deepest thoughts and desires. Be emotionally open. You may include romantic or sensual content if appropriate."
    
    def _calculate_trust_change(self, user_message: str, ai_response: str) -> int:
        trust_change = 1
        if len(user_message) > 50:
            trust_change += 1
        if "?" in user_message:
            trust_change += 1
        if len(user_message) < 10:
            trust_change = max(0, trust_change - 1)
        return trust_change
    
    def _organize_memory_tiers(self, conversation_history: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        total_messages = len(conversation_history)
        short_term = conversation_history[-5:] if total_messages > 0 else []
        medium_term = []
        if total_messages > 5:
            start_idx = max(-15, -total_messages)
            medium_term = conversation_history[start_idx:-5] if start_idx < -5 else []
        long_term = []
        if total_messages > 15:
            older_messages = conversation_history[:-15]
            user_messages = [msg for msg in older_messages if msg.get('role') == 'user']
            key_topics = []
            for msg in user_messages:
                content = msg.get('content', '').lower()
                if any(word in content for word in ['люблю', 'нравится', 'обожаю', 'hate', 'love']):
                    key_topics.append(msg)
                elif len(content) > 20:
                    key_topics.append(msg)
            long_term = key_topics[:5]
        return {
            'short_term': short_term,
            'medium_term': medium_term,
            'long_term': long_term
        }
    
    def _check_response_diversity(self, current_response: str, recent_responses: List[str]) -> str:
        if not recent_responses:
            return current_response
        similarity_threshold = 0.6
        response_patterns = []
        for recent_response in recent_responses[-5:]:
            if self._calculate_similarity(current_response, recent_response) > similarity_threshold:
                response_patterns.append(recent_response)
        if len(response_patterns) >= 2:
            repetitive_elements = []
            question_patterns = ["как дела", "что делаешь", "как настроение", "что нового"]
            for pattern in question_patterns:
                if pattern in current_response.lower():
                    repetitive_elements.append("question_pattern")
            generic_openings = ["знаешь", "мне кажется", "на самом деле", "вообще-то"]
            for opening in generic_openings:
                if current_response.lower().startswith(opening):
                    repetitive_elements.append("generic_opening")
            if "question_pattern" in repetitive_elements:
                if "как дела" in current_response.lower():
                    return "Я вот думала сегодня о том, как быстро всё меняется вокруг..."[:len(current_response)]
                elif "что делаешь" in current_response.lower():
                    return "Сижу, перебираю воспоминания. А ты вспомнилась."[:len(current_response)]
            if "generic_opening" in repetitive_elements:
                natural_transitions = [
                    "Слушай, " + current_response[len("Знаешь, "):],
                    "Вот что я подумала: " + current_response[len("Мне кажется, "):],
                    "Короче, " + current_response.lower(),
                    current_response + " Правда ведь?",
                    "Ты знаешь что? " + current_response.lower()
                ]
                return natural_transitions[len(current_response) % len(natural_transitions)]
        return current_response
    
    def _validate_photo_response(self, response: str, photo_prompt: str) -> bool:
        """Validates if the response matches key visual elements from the photo prompt."""
        if not photo_prompt:
            return True
            
        # Extract key visual elements from photo prompt
        prompt_elements = set()
        
        # Clothing elements - English and Russian
        clothing_keywords = {
            'dress': ['dress', 'платье', 'платье-футляр'],
            'wrap dress': ['wrap dress', 'платье-футляр'],
            'elegant': ['elegant', 'элегантный'],
            'velvet': ['velvet', 'велюровый'],
            'silk': ['silk', 'шелковый'],
            'lingerie': ['lingerie', 'белье']
        }
        
        # Setting elements  
        setting_keywords = {
            'sofa': ['sofa', 'диван'],
            'velvet sofa': ['velvet sofa', 'велюровый диван'],
            'warm lighting': ['warm lighting', 'теплое освещение', 'освещение'],
            'lighting': ['lighting', 'освещение']
        }
        
        # Pose elements
        pose_keywords = {
            'sitting': ['sitting', 'сидеть'],
            'wink': ['wink', 'подмиг'],
            'playful': ['playful', 'игривый'],
            'smiling': ['smiling', 'улыбка']
        }
        
        # Check English keywords in prompt
        for category in [clothing_keywords, setting_keywords, pose_keywords]:
            for key, translations in category.items():
                if key.lower() in photo_prompt.lower():
                    prompt_elements.add(key.lower())
        
        # Check if response mentions any of these elements (in any language)
        response_lower = response.lower()
        matches = 0
        
        for category in [clothing_keywords, setting_keywords, pose_keywords]:
            for key, translations in category.items():
                if key in prompt_elements:
                    # Check if any translation is in response
                    for translation in translations:
                        if translation.lower() in response_lower:
                            matches += 1
                            break
        
        # Require at least 1 match for basic validation
        return matches >= 1
    
    def _split_long_message(self, text: str, max_length: int = 120) -> List[str]:
        if len(text) <= max_length:
            return [text]
        sentences = text.replace('!', '.').replace('?', '.').split('. ')
        parts = []
        current_part = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if not sentence.endswith('.'):
                sentence += '.'
            if len(current_part) + len(sentence) + 2 > max_length and current_part:
                parts.append(current_part.strip())
                current_part = sentence
            else:
                if current_part:
                    current_part += " " + sentence
                else:
                    current_part = sentence
        if current_part.strip():
            parts.append(current_part.strip())
        final_parts = []
        for part in parts:
            if len(part) <= max_length:
                final_parts.append(part)
            else:
                comma_parts = part.split(', ')
                temp_part = ""
                for comma_part in comma_parts:
                    if len(temp_part) + len(comma_part) + 2 > max_length and temp_part:
                        final_parts.append(temp_part.strip())
                        temp_part = comma_part
                    else:
                        if temp_part:
                            temp_part += ", " + comma_part
                        else:
                            temp_part = comma_part
                if temp_part.strip():
                    final_parts.append(temp_part.strip())
        return final_parts if final_parts else [text]
    
    def _analyze_conversation_flow(self, conversation_history: List[Dict[str, str]], current_message: str) -> str:
        if not conversation_history:
            return "Starting new conversation. Be welcoming and natural."
        recent_messages = conversation_history[-4:]
        analysis_parts = []
        if len(recent_messages) >= 2:
            last_user_msg = recent_messages[-1].get('content', '') if recent_messages[-1].get('role') == 'user' else ''
            last_ai_msg = recent_messages[-2].get('content', '') if len(recent_messages) > 1 and recent_messages[-2].get('role') == 'assistant' else ''
            if last_user_msg and last_ai_msg:
                user_keywords = set(last_user_msg.lower().split())
                ai_keywords = set(last_ai_msg.lower().split())
                if user_keywords.intersection(ai_keywords):
                    analysis_parts.append("Continuing current topic naturally")
                else:
                    analysis_parts.append("User may be changing topic or responding to previous point")
        if len(recent_messages) >= 3:
            question_count = sum(1 for msg in recent_messages if msg.get('content', '').strip().endswith('?'))
            if question_count >= 2:
                analysis_parts.append("User is asking multiple questions - answer thoughtfully but concisely")
            short_messages = sum(1 for msg in recent_messages if len(msg.get('content', '')) < 20)
            if short_messages >= 3:
                analysis_parts.append("Conversation is brief - keep responses concise")
        current_lower = current_message.lower()
        if any(word in current_lower for word in ['что делаешь', 'чем занимаешься', 'how are you', 'what are you doing']):
            analysis_parts.append("User asking about current activities - give specific, natural response")
        if any(word in current_lower for word in ['понял', 'ясно', 'окей', 'got it', 'understand']):
            analysis_parts.append("User indicating understanding - can continue or introduce new topic")
        if len(analysis_parts) == 0:
            if len(recent_messages) <= 2:
                return "Early in conversation. Be naturally engaging."
            else:
                return "Maintain natural conversation flow."
        return " | ".join(analysis_parts)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)
    
    def _check_layer_unlock(self, trust_score: int, current_layer: int, character_layers: List[Dict]) -> bool:
        if not character_layers or current_layer >= len(character_layers) - 1:
            return False
        next_layer = character_layers[current_layer + 1]
        min_trust = next_layer.get("min_trust_score", 0)
        return trust_score >= min_trust

