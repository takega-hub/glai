import asyncio
from datetime import datetime, timedelta

from database.connection import get_db
from services.ai_dialogue import AIDialogueEngine
from services.notification_service import notification_service

RE_ENGAGEMENT_TIERS = [
    {"name": "1h", "min_inactive": timedelta(hours=1), "max_inactive": timedelta(hours=3), "message_type": "casual"},
    {"name": "3h", "min_inactive": timedelta(hours=3), "max_inactive": timedelta(days=1), "message_type": "checkin"},
    {"name": "1d", "min_inactive": timedelta(days=1), "max_inactive": timedelta(days=3), "message_type": "greeting"},
    {"name": "3d", "min_inactive": timedelta(days=3), "max_inactive": timedelta(days=7), "message_type": "story"},
]

async def run_re_engagement_check():
    """
    Finds inactive users and sends them proactive messages based on a stepped logic.
    This function is intended to be run periodically (e.g., every 30 minutes).
    """
    print("--- Running Re-engagement Check ---")
    db_gen = get_db()
    db = await anext(db_gen)
    ai_engine = AIDialogueEngine()

    try:
        async with db.acquire() as connection:
            for tier in RE_ENGAGEMENT_TIERS:
                users = await connection.fetch(
                    """SELECT u.id as user_id, u.username, ucs.character_id, ucs.last_message_date, ucs.notifications_enabled
                       FROM users u
                       JOIN user_character_state ucs ON u.id = ucs.user_id
                       WHERE ucs.last_message_date IS NOT NULL
                       AND (ucs.notifications_enabled IS NULL OR ucs.notifications_enabled = true)
                       AND ucs.last_message_date <= $1
                       AND ucs.last_message_date > $2""",
                    datetime.utcnow() - tier["min_inactive"],
                    datetime.utcnow() - tier["max_inactive"]
                )

                for user in users:
                    await process_user(connection, user, tier["message_type"], ai_engine, db)

    finally:
        await db_gen.aclose()
    print("--- Re-engagement Check Finished ---")

async def process_user(connection, user_record, message_type, ai_engine, db):
    """Generates a message, saves it to DB, and sends a push notification for a single user."""
    try:
        user_id = user_record['user_id']
        character_id = user_record['character_id']

        print(f"Processing user {user_id} for a '{message_type}' re-engagement.")

        character = await connection.fetchrow("SELECT * FROM characters WHERE id = $1", character_id)
        if not character:
            return

        import json
        user_state = await connection.fetchrow(
            "SELECT * FROM user_character_state WHERE user_id = $1 AND character_id = $2",
            user_id, character_id
        )

        if user_state.get('notifications_enabled') is False:
            print(f"User {user_id} has notifications disabled. Skipping.")
            return

        conversation_history = json.loads(user_state['conversation_history'] or "[]")

        proactive_message = await ai_engine.generate_proactive_message(
            character_data=dict(character),
            user_data={
                "user_id": user_id,
                "username": user_record['username'],
                "trust_score": user_state['trust_score'],
                "last_message_date": user_state['last_message_date'],
                "conversation_history": conversation_history
            },
            message_type=message_type
        )

        if proactive_message.get('unsubscribed'):
            print(f"User opted out of notifications. Disabling for user {user_id}, character {character_id}")
            await connection.execute(
                "UPDATE user_character_state SET notifications_enabled = false WHERE user_id = $1 AND character_id = $2",
                user_id, character_id
            )
            return

        conversation_history.append({"role": "assistant", "content": proactive_message['message']})

        await connection.execute(
            """INSERT INTO messages (character_id, user_id, response, created_at) VALUES ($1, $2, $3, NOW())""",
            character_id, user_id, proactive_message['message']
        )

        await connection.execute(
            "UPDATE user_character_state SET conversation_history = $1, last_message_date = NOW() WHERE user_id = $2 AND character_id = $3",
            json.dumps(conversation_history),
            user_id,
            character_id
        )

        await notification_service.send_push_notification(
            db_connection=db,
            user_id=str(user_id),
            title=character['display_name'] or character['name'],
            body=proactive_message['message'],
            data={
                "character_id": str(character_id),
                "type": "re_engagement"
            }
        )

    except Exception as e:
        print(f"Failed to process user {user_record['user_id']}: {e}")

if __name__ == "__main__":
    print("Starting manual re-engagement scheduler...")
    asyncio.run(run_re_engagement_check())
