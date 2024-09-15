import os
from django.core.asgi import get_asgi_application
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ptproject.settings')

django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import pt_app.routing  # Import the routing of your app

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            pt_app.routing.websocket_urlpatterns
        )
    ),
})