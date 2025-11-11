from django.urls import re_path
import utils.consumer as consumers
from utils.consumer import TokenDisplayConsumer

websocket_urlpatterns = [
    re_path(r'ws/token-display/$', TokenDisplayConsumer.as_asgi()),
]