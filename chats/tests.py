from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
