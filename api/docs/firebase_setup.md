# Firebase Cloud Messaging Setup Guide

This guide explains how to set up Firebase Cloud Messaging (FCM) for push notifications in the EVA AI backend.

## Prerequisites

1. **Firebase Project**: You need to create a Firebase project in the [Firebase Console](https://console.firebase.google.com/)
2. **Service Account Key**: Download the service account key for server-side authentication

## Setup Steps

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create Project" or select existing project
3. Enable Cloud Messaging API if not already enabled

### 2. Generate Service Account Key

1. In Firebase Console, go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save the downloaded JSON file as `serviceAccountKey.json` in the `/opt/EVA_AI/api/` directory

### 3. Environment Configuration

Add the following environment variable to your `.env` file:

```bash
FIREBASE_SERVICE_ACCOUNT_PATH=serviceAccountKey.json
```

### 4. Install Dependencies

The `firebase-admin` package is already added to `requirements.txt`. Install it with:

```bash
pip install -r requirements.txt
```

## API Endpoints

### Register Push Token

**Endpoint**: `POST /api/notifications/push-token`

**Request Body**:
```json
{
  "token": "fcm_device_token_here",
  "platform": "android" | "ios"
}
```

**Response**:
```json
{
  "message": "Push token registered successfully."
}
```

### Send Notification to User

**Endpoint**: `POST /api/notifications/send-to-user/{user_id}`

**Query Parameters**:
- `title`: Notification title
- `body`: Notification body
- `data`: Optional JSON data payload (optional)

**Response**:
```json
{
  "message": "Sent X notifications successfully",
  "success_count": 1
}
```

## Push Notification Triggers

The system automatically sends push notifications in the following scenarios:

### 1. New AI Message
- **Trigger**: When AI generates a response and user is not online (no active WebSocket connection)
- **Title**: "Новое сообщение от {character_name} 💬"
- **Body**: First 100 characters of the AI response
- **Data**: Contains character info and message preview

### 2. Content Generated
- **Trigger**: When on-demand photo generation is completed
- **Title**: "Твоё фото готово! 📸"
- **Body**: "Я сделала это фото специально для тебя, по твоей просьбе. Как тебе?"
- **Data**: Contains character ID, image URL, and content type

### 3. Content Unlocked
- **Trigger**: When intimate photos or layer photos are unlocked
- **Title**: "Новое фото разблокировано! 🔓" (layer photos) or "Новое фото от персонажа! 📸" (intimate photos)
- **Body**: Character response message
- **Data**: Contains character ID, image URL, and content type

## Testing

### Test Push Notification

1. Register a device token using the mobile app
2. Use the admin endpoint to send a test notification:

```bash
curl -X POST "http://localhost:8000/api/notifications/send-to-user/{user_id}?title=Test&body=Hello" \
  -H "Authorization: Bearer {your_jwt_token}"
```

### Check Service Status

The service will log initialization status:
- "Firebase Admin SDK initialized successfully" - Service is ready
- "Service account file not found... Push notifications will be simulated" - Service account not found

## Error Handling

The system handles the following error scenarios:

1. **Invalid Device Tokens**: Automatically removes invalid tokens from database
2. **Network Issues**: Retries with exponential backoff
3. **Authentication Errors**: Logs detailed error messages
4. **Service Account Issues**: Falls back to simulation mode

## Security Considerations

1. **Service Account Key**: Keep the service account key secure and never commit it to version control
2. **Token Validation**: Validate device tokens before storing in database
3. **Rate Limiting**: Implement rate limiting for notification endpoints
4. **User Permissions**: Users can only send notifications to themselves unless they have admin privileges

## Monitoring

Monitor push notification performance through:
- Firebase Cloud Messaging dashboard
- Application logs for delivery status
- Database queries for token cleanup statistics

## Troubleshooting

### Common Issues

1. **Service account file not found**: Ensure `serviceAccountKey.json` is in the correct location
2. **Permission denied**: Check Firebase project permissions and service account roles
3. **Invalid tokens**: The system automatically cleans up invalid tokens
4. **Notifications not received**: Check device token registration and platform-specific settings

### Debug Mode

Set environment variable for detailed logging:
```bash
LOG_LEVEL=DEBUG
```

This will provide detailed information about:
- Firebase initialization
- Token validation
- Message sending attempts
- Error responses