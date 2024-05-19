import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, ChatSession, User
from django.db.models import Q
from django.db import models


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id_1 = self.scope['url_route']['kwargs']['user_id_1']
        self.user_id_2 = self.scope['url_route']['kwargs']['user_id_2']

        
        self.room_group_name = self.construct_room_name(self.user_id_1, self.user_id_2)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        sender_id = text_data_json['senderId']
        content = text_data_json['content']

        # Use await when calling save_message
        await self.save_message(sender_id, self.user_id_1, self.user_id_2, content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'sender': sender_id,
                    'content': content,
                },
            }
        )
  
    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))
    def construct_room_name(self, user_id_1, user_id_2):
        return f"chat_{min(user_id_1, user_id_2)}_{max(user_id_1, user_id_2)}"
    
    @database_sync_to_async
    def get_or_create_chat_session(self, user_id_1, user_id_2):
        # Your logic to ensure two values are returned
        user1 = User.objects.get(id=user_id_1)
        user2 = User.objects.get(id=user_id_2)
        chat_sessions = ChatSession.objects.filter(
            participants__id__in=[user1.id, user2.id]
        ).annotate(
            participants_count=models.Count('participants')
        ).filter(
            participants_count=2
        )
        if chat_sessions.exists():
            return chat_sessions.first(), False
        else:
            chat_session = ChatSession.objects.create()
            chat_session.participants.add(user1, user2)
            return chat_session, True

    async def save_message(self, sender_id, user_id_1, user_id_2, content):
        sender = await database_sync_to_async(User.objects.get)(id=sender_id)
        chat_session, created = await self.get_or_create_chat_session(user_id_1, user_id_2)
        message = await database_sync_to_async(Message.objects.create)(
        sender=sender, content=content, chat_session=chat_session
        )
        return message