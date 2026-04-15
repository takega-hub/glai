import firebase_admin
from firebase_admin import credentials, messaging
import os
from typing import List, Optional
from decouple import config

class NotificationService:
    def __init__(self):
        self.initialized = False
        self.cert_path = config("FIREBASE_SERVICE_ACCOUNT_JSON", default="")

        if self.cert_path and os.path.exists(self.cert_path):
            try:
                cred = credentials.Certificate(self.cert_path)
                firebase_admin.initialize_app(cred)
                self.initialized = True
                print("Firebase Admin initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize Firebase Admin: {e}")
        else:
            print("Firebase service account JSON not found. Notifications will be disabled.")

    async def send_push_notification(
        self,
        db_connection,
        user_id: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ):
        """Sends a push notification to all devices registered for a user"""
        if not self.initialized:
            return

        # Get device tokens from database
        devices = await db_connection.fetch(
            "SELECT device_token FROM user_devices WHERE user_id = $1",
            user_id
        )

        if not devices:
            return

        tokens = [d["device_token"] for d in devices]

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
        )

        try:
            response = messaging.send_multicast(message)
            print(f"Successfully sent {response.success_count} notifications; failures: {response.failure_count}")
        except Exception as e:
            print(f"Error sending push notification: {e}")

notification_service = NotificationService()
