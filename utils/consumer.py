import json
from channels.generic.websocket import AsyncWebsocketConsumer


class BaseSocketConsumer(AsyncWebsocketConsumer):
    '''A base WebSocket consumer to handle common functionality like connect, disconnect, and receive.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = None
    
    async def connect(self):
        # Connect to the group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(" WebSocket connected")

    async def disconnect(self, close_code):
        # Remove connection when disconnected
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(" WebSocket disconnected")

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming messages from WebSocket
        data = json.loads(text_data)
        print("Received data:", data)
        # Echo the received message back to the client


class TokenDisplayConsumer(BaseSocketConsumer):
    '''WebSocket consumer for token display updates.
       It inherits from BaseSocketConsumer to handle token display specific functionality.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "token_display_group"
        # group name(it is the group identifier, client subscribe for this group, one group can have multiple clients) for token display updates

    async def token_display_api_update(self, event):
        '''Handles token display update events. Sends the updated token information to the WebSocket client.'''
        
        data = event['data']
        
        # data is the payload sent from server to client
        # type is the type of event(function name to be called on client side)
        await self.send(text_data=json.dumps({
            'type': "message from server to client",
            'data': data
        }))