import asyncio
from datetime import datetime, timedelta

from database.connection import get_db
from services.ai_dialogue import AIDialogueEngine
from services.push_notification_service import PushNotificationService

async def run_re_engagement_check():
    """
    Finds inactive users and sends them proactive messages based on a stepped logic.
    This function is intended to be run periodically (e.g., every hour).
    """
    print("--- Running Re-engagement Check ---")
    db_gen = get_db()
    db = await anext(db_gen)
    ai_engine = AIDialogueEngine()
    push_service = PushNotificationService()

    try:
        async with db.acquire() as connection:
            # 1. Find users who have been inactive for more than 24 hours
            # but less than 3 days. Send a simple greeting.
            inactive_users_tier1 = await connection.fetch(
                """SELECT u.id as user_id, u.username, ucs.character_id, ucs.last_message_date
                   FROM users u
                   JOIN user_character_state ucs ON u.id = ucs.user_id
                   WHERE ucs.last_message_date BETWEEN $1 AND $2""",
                datetime.utcnow() - timedelta(days=3),
                datetime.utcnow() - timedelta(days=1)
            )

            for user in inactive_users_tier1:
                await process_user(connection, user, "greeting", ai_engine, push_service)

            # 2. Find users inactive for more than 3 days but less than 7.
            # Send a more engaging story or question.
            inactive_users_tier2 = await connection.fetch(
                """SELECT u.id as user_id, u.username, ucs.character_id, ucs.last_message_date
                   FROM users u
                   JOIN user_character_state ucs ON u.id = ucs.user_id
                   WHERE ucs.last_message_date BETWEEN $1 AND $2""",
                datetime.utcnow() - timedelta(days=7),
                datetime.utcnow() - timedelta(days=3)
            )

            for user in inactive_users_tier2:
                await process_user(connection, user, "story", ai_engine, push_service)

    finally:
        await db_gen.aclose()
    print("--- Re-engagement Check Finished ---")

async def process_user(connection, user_record, message_type, ai_engine, push_service):
    """Generates a message and sends a push notification for a single user."""
    try:
        print(f"Processing user {user_record['user_id']} for a '{message_type}' re-engagement.")
        character = await connection.fetchrow("SELECT * FROM characters WHERE id = $1", user_record['character_id'])
        if not character:
            return

        user_state = await connection.fetchrow("SELECT * FROM user_character_state WHERE user_id = $1 AND character_id = $2", user_record['user_id'], user_record['character_id'])

        proactive_message = await ai_engine.generate_proactive_message(
            character_data=dict(character),
            user_data={
                "user_id": user_record['user_id'],
                "username": user_record['username'],
                "trust_score": user_state['trust_score'],
                "last_message_date": user_state['last_message_date']
            },
            message_type=message_type
        )

        # Get device token
        device = await connection.fetchrow("SELECT device_token FROM user_devices WHERE user_id = $1", user_record['user_id'])
        if device and device['device_token']:
            await push_service.send_push_notification(
                device_token=device['device_token'],
                message=f"{character['display_name']}: {proactive_message['message']}"
            )
        else:
            print(f"No device token found for user {user_record['user_id']}. Skipping push.")

    except Exception as e:
        print(f"Failed to process user {user_record['user_id']}: {e}")

if __name__ == "__main__":
    print("Starting manual re-engagement scheduler...")
    asyncio.run(run_re_engagement_check())
