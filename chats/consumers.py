import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import (
    Conversation,
    ConversationMember,
    Message,
    Attachment,
)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        if (
            not self.user.is_authenticated
            or not await self.user_is_member(self.user, self.room_name)
        ):
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        if not text_data:
            return

        data = json.loads(text_data)

        message_text = (data.get("message") or "").strip()

        if not message_text:
            return

        message = await self.save_message(message_text)

        attachment = await self.get_gif_attachment(message.id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message.text,
                "message_id": message.id,
                "sender_id": message.sender.id,
                "sender_username": message.sender.username,
                "sender_display_name": (
                    message.sender.display_name
                    or message.sender.username
                ),
                "sender_profile_picture": (
                    message.sender.profile_picture.url
                    if message.sender.profile_picture
                    else ""
                ),
                "gif_url": attachment.gif_url if attachment else "",
                "gif_id": attachment.gif_id if attachment else "",
                "created_at": message.created_at.isoformat(),
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "message_id": event["message_id"],
                    "sender_id": event["sender_id"],
                    "sender_username": event["sender_username"],
                    "sender_display_name": event["sender_display_name"],
                    "sender_profile_picture": event["sender_profile_picture"],
                    "gif_url": event["gif_url"],
                    "gif_id": event["gif_id"],
                    "created_at": event["created_at"],
                }
            )
        )

    @database_sync_to_async
    def user_is_member(self, user, room_name):
        try:
            conversation = Conversation.objects.get(pk=room_name)
        except Conversation.DoesNotExist:
            return False

        return ConversationMember.objects.filter(
            conversation=conversation,
            user=user,
        ).exists()

    @database_sync_to_async
    def save_message(self, text):
        conversation = Conversation.objects.get(pk=self.room_name)

        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            text=text,
        )

        conversation.save(update_fields=["updated_at"])

        return message

    @database_sync_to_async
    def get_gif_attachment(self, message_id):
        return (
            Attachment.objects.filter(
                message_id=message_id,
                file_type="gif",
            )
            .first()
        )