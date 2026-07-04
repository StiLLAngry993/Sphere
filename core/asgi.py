"""
ASGI config for core project.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application


django.setup()

import chats.routing

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(chats.routing.websocket_urlpatterns)),
    }
)
