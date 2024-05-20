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
        event_type = text_data_json.get('type')

        # Dispatch to the appropriate handler based on the type of the message
        if event_type == 'message':
            await self.handle_chat_message(text_data_json)
        elif event_type == 'trainer-request-sent':
            await self.handle_trainer_request(text_data_json)
        elif event_type == 'trainer-request-accepted':
            await self.handle_accepted_response(text_data_json)
        elif event_type == 'trainer-rejected-accepted':
            await self.handle_rejected_response(text_data_json)

    async def handle_chat_message(self, data):
        # Prepare and send message to both the sender's and recipient's personal channel
        message_data = {
            'type': 'chat_message',
            'message': {
                'sender': data['senderId'],
                'recipient': data['recipientId'],
                'content': data['content'],
            },
        }
        # Save the message
        await self.save_message(data['senderId'],  data['recipientId'], data['content'])

        await self.channel_layer.group_send(f"user_{data['senderId']}", message_data)
        await self.channel_layer.group_send(f"user_{data['recipientId']}", message_data)

    async def handle_trainer_request(self, data):
        # Directly relay the trainer request data to the recipient's channel
        request_data = {
            'type': 'forward_trainer_request',
            'request': {
                'id': data['id'],
                'from_user': data['from_user'],
                'to_user': data['to_user'],
                'created_at': data['created_at'],
                'is_active': data['is_active']
            },
        }
        await self.channel_layer.group_send(f"user_{data['to_user']}", request_data)

    async def handle_accepted_response(self, data):
        # Process trainer request responses (accepted or rejected)
        response_data = {
            'type': 'forward_request_accepted',  # This will be either 'trainer-request-accepted' or 'trainer-request-rejected'
            'data': {
                'id': data['id'],
                'from_user': data['from_user'],
                'to_user': data['to_user']
            }
        }
        await self.channel_layer.group_send(f"user_{data['to_user']}", response_data)

    async def handle_rejected_response(self, data):
        # Process trainer request responses (accepted or rejected)
        response_data = {
            'type': 'forward_request_rejected',  # This will be either 'trainer-request-accepted' or 'trainer-request-rejected'
            'data': {
                'id': data['id'],
                'from_user': data['from_user'],
                'to_user': data['to_user']
            }
        }
        await self.channel_layer.group_send(f"user_{data['to_user']}", response_data)

    async def chat_message(self, event):
        # Send chat message data to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def forward_trainer_request(self, event):
        # Forward the trainer request data to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'trainer-request-sent',
            'data': event['request']
        }))

    async def forward_request_accepted(self, event):
        # Handler for when a trainer request is accepted
        await self.send(text_data=json.dumps({
            'type': 'trainer_request_accepted',
            'data': event['data']
        }))

    async def forward_request_rejected(self, event):
        # Handler for when a trainer request is rejected
        await self.send(text_data=json.dumps({
            'type': 'trainer_request_rejected',
            'data': event['data']
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