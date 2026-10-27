import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Reject anonymous/unauthenticated users
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Ensure user is an actual participant in this conversation
        is_participant = await self.verify_participant(self.user, self.room_id)
        if not is_participant:
            await self.close(code=4003)
            return

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Broadcast user online / presence
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'username': self.user.username,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            # Broadcast user offline
            if self.user.is_authenticated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_status',
                        'username': self.user.username,
                        'status': 'offline'
                    }
                )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type', 'chat_message')

            if msg_type == 'chat_message':
                content = data.get('content', '').strip()
                if not content:
                    return

                # Save message to database
                message_record = await self.save_message(self.user, self.room_id, content)

                # Send message event to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message_event',
                        'message_id': message_record['id'],
                        'content': message_record['content'],
                        'sender': message_record['sender'],
                        'sender_avatar': message_record['sender_avatar'],
                        'timestamp': message_record['timestamp'],
                        'message_type': 'text',
                        'attachment_url': '',
                        'attachment_name': '',
                        'attachment_size': '',
                    }
                )

            elif msg_type == 'typing':
                # Broadcast typing indicator
                is_typing = data.get('is_typing', False)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'username': self.user.username,
                        'is_typing': is_typing
                    }
                )

            elif msg_type == 'mark_read':
                await self.mark_messages_read(self.room_id, self.user)

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    # Handlers called by group_send
    async def chat_message_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'id': event.get('message_id'),
            'content': event.get('content', ''),
            'sender': event.get('sender'),
            'sender_avatar': event.get('sender_avatar', ''),
            'timestamp': event.get('timestamp'),
            'message_type': event.get('message_type', 'text'),
            'attachment_url': event.get('attachment_url', ''),
            'attachment_name': event.get('attachment_name', ''),
            'attachment_size': event.get('attachment_size', ''),
        }))

    async def typing_indicator(self, event):
        # Do not echo own typing status back to sender
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'username': event['username'],
            'status': event['status']
        }))

    # Database helpers
    @database_sync_to_async
    def verify_participant(self, user, room_id):
        return Conversation.objects.filter(id=room_id, participants=user).exists()

    @database_sync_to_async
    def save_message(self, user, room_id, content):
        conv = Conversation.objects.get(id=room_id)
        msg = Message.objects.create(conversation=conv, sender=user, content=content)
        conv.save()  # Updates conversation updated_at timestamp

        avatar_url = user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else ''
        return {
            'id': msg.id,
            'content': msg.content,
            'sender': user.username,
            'sender_avatar': avatar_url,
            'timestamp': msg.timestamp.strftime('%I:%M %p')
        }

    @database_sync_to_async
    def mark_messages_read(self, room_id, user):
        Message.objects.filter(conversation_id=room_id).exclude(sender=user).update(is_read=True)
