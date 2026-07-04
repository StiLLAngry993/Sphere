from django.urls import re_path
# We will create the ChatConsumer in the next step, so ignore any warnings for now!
from . import consumers 

websocket_urlpatterns = [
    # This url matches ws://your-domain/ws/chat/ROOM_NAME/
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]