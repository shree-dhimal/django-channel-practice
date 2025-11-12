from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from utils.redis_config import RedisSetup

APPLICATION = config('APPLICATION')
channel_layer = get_channel_layer()


def connect_to_channel_layer(group_name: str,function_name: str, response_data: dict | None = None, action: str | None = None):
    
    # channel_layer = get_channel_layer()
    if not channel_layer:
        print("No Channel layer Configured or Redis client not connected")
        return
    
    if APPLICATION == "ASGI":
        '''Connects to the channel layer. Returns the channel layer instance.'''
        
        print("Connected to channel layer")

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": function_name,
                "data": response_data
            }
        )
        print("Message sent to channel layer")
    else:
        redis_obj = RedisSetup()
        redis_connection = redis_obj.connect()
        ''' if the application is WSGI, use Redis to publish and subscribe messages'''

        if not redis_connection["status"]:
           print("Failed to connect to Redis:", redis_connection["message"])
           return
        message = {
            "type": action,
            "data": response_data
        }
        publish_response = redis_obj.publish_message_to_redis(channel=group_name, message=message)
        if not publish_response["status"]:
            print("Failed to publish message to Redis:", publish_response["message"])
            return
        # send_message_to_websocket_via_redis(redis_obj, group_name, function_name)
        
        
        
        
        
def send_token_display_update(data):
    '''Sends token display update to the channel layer.'''
    connect_to_channel_layer(
        group_name="token_display_group",
        function_name="token_display_api_update",
        response_data=data
    )

# this is the example function to send message to websocket via redis we can configure to a ASGI Application to send message to websocket clients like Microservice architecture
async def send_message_to_websocket_via_redis(redis_obj: RedisSetup, group_name: str, function_name: str):
    '''Sends a message to the WebSocket via Redis.'''

    try:

        subscribe_response = redis_obj.receive_message_from_redis(channel=group_name)
        if not subscribe_response["status"]:
            print("Failed to subscribe message from Redis:", subscribe_response["message"])
            return
        
        await channel_layer.group_send(
            group_name,
            {
                "type": function_name,  # this must match the function in your consumer
                "data": subscribe_response["data"],
            },
        )
    except Exception as e:
        print("Error sending message to WebSocket via Redis:", str(e))

