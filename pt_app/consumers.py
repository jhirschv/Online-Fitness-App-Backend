import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, ChatSession
from django.db.models import Q

User = get_user_model()

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
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
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
    def get_or_create_chat_session(self, sender_id, receiver_id):
        sender_id, receiver_id = int(sender_id), int(receiver_id)
        
        sessions = ChatSession.objects.filter(participants__id=sender_id).filter(participants__id=receiver_id)
        
        for session in sessions:
            if session.participants.count() == 2:
                return session, False
        
        chat_session = ChatSession.objects.create()
        chat_session.participants.add(sender_id, receiver_id)
        return chat_session, True

    @database_sync_to_async
    def save_message(self, sender, user_id_1, user_id_2, content):
        sender = User.objects.get(id=sender)
        receiver_id = int(user_id_1) if int(user_id_1) != sender.id else int(user_id_2)
        receiver = User.objects.get(id=receiver_id)
        chat_session, created = self.get_or_create_chat_session(sender.id, receiver_id)
        Message.objects.create(sender=sender, receiver=receiver, content=content, chat_session=chat_session)