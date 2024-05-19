import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, ChatSession, User
from django.db.models import Q
from django.db import models


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.personal_channel_name = f"user_{self.user_id}"

        # Subscribe to personal channel
        await self.channel_layer.group_add(
            self.personal_channel_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Unsubscribe from personal channel
        await self.channel_layer.group_discard(
            self.personal_channel_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        sender_id = text_data_json['senderId']
        recipient_id = text_data_json['recipientId']
        content = text_data_json['content']

        # Save the message
        await self.save_message(sender_id, recipient_id, content)

        # Prepare message data
        message_data = {
            'type': 'chat_message',
            'message': {
                'sender': sender_id,
                'content': content,
            },
        }

        # Send message to both the sender's and recipient's personal channel
        await self.channel_layer.group_send(f"user_{sender_id}", message_data)
        await self.channel_layer.group_send(f"user_{recipient_id}", message_data)

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))
    
    @database_sync_to_async
    def get_or_create_chat_session(self, user_id_1, user_id_2):
        # Ensure the user IDs are in a consistent order
        user_id_1, user_id_2 = sorted([user_id_1, user_id_2])

        # Retrieve users from the database
        user1, user2 = User.objects.get(id=user_id_1), User.objects.get(id=user_id_2)

        # Check for an existing chat session between these two users
        chat_sessions = ChatSession.objects.filter(
            participants__id__in=[user1.id, user2.id]
        ).annotate(participants_count=models.Count('participants')).filter(participants_count=2)

        if chat_sessions.exists():
            return chat_sessions.first(), False
        else:
            # Create a new chat session and add both participants
            chat_session = ChatSession.objects.create()
            chat_session.participants.add(user1, user2)
            return chat_session, True

    async def save_message(self, sender_id, recipient_id, content):
        # Retrieve sender and recipient from the database
        sender = await database_sync_to_async(User.objects.get)(id=sender_id)
        recipient = await database_sync_to_async(User.objects.get)(id=recipient_id)

        # Get or create a chat session between sender and recipient
        chat_session, created = await self.get_or_create_chat_session(sender_id, recipient_id)

        # Create and save the new message
        message = await database_sync_to_async(Message.objects.create)(
            sender=sender,
            content=content,
            chat_session=chat_session
        )
        return message