import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .consumers import ChatConsumer
from .models import Conversation, ConversationMember


class ChatLayoutViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="secret123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="friend",
            email="friend@example.com",
            password="secret123",
        )
        self.conv = Conversation.objects.create(is_group=False)
        ConversationMember.objects.create(conversation=self.conv, user=self.user)
        ConversationMember.objects.create(conversation=self.conv, user=self.other_user)

    def test_inbox_uses_shared_chat_layout(self):
        self.client.login(username="tester", password="secret123")
        response = self.client.get(reverse("chats:inbox"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chats/chat_layout.html")
        self.assertContains(response, "Your Messages")
        self.assertContains(response, "Pick a conversation")

    def test_room_uses_shared_chat_layout_with_selected_conversation(self):
        self.client.login(username="tester", password="secret123")
        response = self.client.get(reverse("chats:room", kwargs={"pk": self.conv.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chats/chat_layout.html")
        self.assertContains(response, "Type a message")

    def test_room_exposes_live_chat_websocket_hook(self):
        self.client.login(username="tester", password="secret123")
        response = self.client.get(reverse("chats:room", kwargs={"pk": self.conv.pk}))

        self.assertContains(response, "__SPHERE_CHAT_WS_URL__")
        self.assertContains(response, "new WebSocket")

    def test_receive_broadcasts_event_to_chat_group(self):
        consumer = ChatConsumer.__new__(ChatConsumer)
        consumer.room_group_name = "chat_123"
        consumer.room_name = "123"
        consumer.user = self.user
        consumer.channel_layer = AsyncMock()

        message = SimpleNamespace(
            id=42,
            sender_id=self.user.id,
            sender=self.user,
            created_at=self.conv.created_at,
        )
        consumer.save_message = AsyncMock(return_value=message)

        async_to_sync(consumer.receive)(json.dumps({"message": "hello"}))

        consumer.channel_layer.group_send.assert_awaited_once()
        payload = consumer.channel_layer.group_send.await_args.args[1]
        self.assertEqual(payload["type"], "chat_message")
