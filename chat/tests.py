import json
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from connectly.asgi import application
from .models import Conversation, Message

class ChatWebSocketTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='Password123!')
        self.user2 = User.objects.create_user(username='user2', password='Password123!')
        self.user3 = User.objects.create_user(username='unauthorized', password='Password123!')
        self.conversation, _ = Conversation.get_or_create_direct_chat(self.user1, self.user2)

    async def test_authenticated_participant_connects(self):
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.conversation.id}/'
        )
        communicator.scope['user'] = self.user1
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_unauthorized_user_connection_rejected(self):
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.conversation.id}/'
        )
        communicator.scope['user'] = self.user3
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_send_and_receive_instant_message(self):
        communicator1 = WebsocketCommunicator(application, f'/ws/chat/{self.conversation.id}/')
        communicator1.scope['user'] = self.user1
        await communicator1.connect()

        communicator2 = WebsocketCommunicator(application, f'/ws/chat/{self.conversation.id}/')
        communicator2.scope['user'] = self.user2
        await communicator2.connect()

        # User1 sends message
        await communicator1.send_json_to({
            'type': 'chat_message',
            'content': 'Hello from user1 via WebSocket!'
        })

        # User2 receives message (drain any presence broadcast if present)
        response = await communicator2.receive_json_from()
        while response.get('type') == 'user_status':
            response = await communicator2.receive_json_from()
        self.assertEqual(response['type'], 'chat_message')
        self.assertEqual(response['content'], 'Hello from user1 via WebSocket!')
        self.assertEqual(response['sender'], 'user1')

        await communicator1.disconnect()
        await communicator2.disconnect()


class ChatAttachmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='Password123!')
        self.user2 = User.objects.create_user(username='user2', password='Password123!')
        self.user3 = User.objects.create_user(username='intruder', password='Password123!')
        self.conversation, _ = Conversation.get_or_create_direct_chat(self.user1, self.user2)

    def generate_dummy_image(self):
        file = BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(file, 'jpeg')
        file.seek(0)
        return SimpleUploadedFile("test_pic.jpg", file.read(), content_type="image/jpeg")

    def test_upload_image_attachment_success(self):
        self.client.login(username='user1', password='Password123!')
        img = self.generate_dummy_image()
        url = reverse('chat_upload', kwargs={'room_id': self.conversation.id})

        response = self.client.post(url, {
            'attachment': img,
            'content': 'Check out this screenshot!'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)
        msg = Message.objects.first()
        self.assertEqual(msg.message_type, 'image')
        self.assertTrue(msg.is_image)
        self.assertEqual(msg.content, 'Check out this screenshot!')
        self.assertEqual(msg.attachment_name, 'test_pic.jpg')

    def test_unauthorized_user_cannot_upload_to_room(self):
        self.client.login(username='intruder', password='Password123!')
        dummy_file = SimpleUploadedFile("doc.txt", b"secret info", content_type="text/plain")
        url = reverse('chat_upload', kwargs={'room_id': self.conversation.id})

        response = self.client.post(url, {'attachment': dummy_file})
        self.assertEqual(response.status_code, 404)  # Get_object_or_404 participant guard
        self.assertEqual(Message.objects.count(), 0)

    def test_reject_oversized_file(self):
        self.client.login(username='user1', password='Password123!')
        # 16 MB oversized mock file
        big_content = b"0" * (16 * 1024 * 1024)
        big_file = SimpleUploadedFile("big.zip", big_content, content_type="application/zip")
        url = reverse('chat_upload', kwargs={'room_id': self.conversation.id})

        response = self.client.post(url, {'attachment': big_file})
        # Handled by model validation / view
        self.assertIn(response.status_code, [400, 500])
