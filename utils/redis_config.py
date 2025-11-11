import redis
import json
from decouple import config

REDIS_CLIENT = config('REDIS_CLIENT', default='127.0.0.1')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)

class RedisSetup:
    def __init__(self):
        self.client =REDIS_CLIENT
        self.port = REDIS_PORT
        self.redis_instance = None

    def connect(self):
        '''Connects to the Redis server.'''

        res = {"status": False, "message": "Failed to connect to Redis"}
        try:
            if self.client and self.port:
                self.redis_instance = redis.StrictRedis(
                host=self.client,
                port=self.port,
                db=0,
                decode_responses=True
            )
                self.redis_instance.ping() # Test the connection
                res["status"] = True
                res["message"] = "Connected to Redis successfully"
                print(res["message"])
                return res
            else:
                self.redis_instance = None
                res["message"] = "please provide redis client and port"
                print(res["message"])   
                return res
        except redis.ConnectionError as e:
            self.redis_instance = None
            res["message"] = f"Redis connection error: {str(e)}"
            print("Redis connection error:", str(e))
            return res
    
    def publish_message_to_redis(self, channel: str, message: dict):
        '''Publishes a message to a Redis channel.
            accepts channel name(unique identifier for the channel, used while subscribing the message) and message dictionary as parameters.
        '''
        res = {"status": False, "message": "redis client not connected"}
        if self.redis_instance:
            try:
                message_str = json.dumps(message)
                self.redis_instance.publish(channel, message_str)
                res["status"] = True
                res["message"] = f"Message published to channel {channel}"
                print(res["message"])
                return res
            except redis.RedisError as e:
                print("Error publishing message to Redis:", str(e))
                res["message"] = f"Error publishing message to Redis : {str(e)}"
                return res
        else:
            print(res["message"])
            return res
    
    def disconnect(self):
        '''Disconnects the Redis client.'''

        res = {"status": False, "message": "Redis client not connected"}

        if self.redis_instance:
            self.redis_instance.close()
            res["status"] = True
            res["message"] = "Redis client disconnected successfully"
            print(res["message"])
            return res
        else:
            print(res["message"])
            return res
    
    def receive_message_from_redis(self, channel: str, callback=None):
        '''Subscribes to a Redis channel and listens for messages.
            accepts channel name(unique identifier for the channel, used while subscribing the message) as parameter.
        '''
        res = {"data": None, "status": False, "message": "No message received"}
        if self.redis_instance:
            try:
                pubsub = self.redis_instance.pubsub()
                pubsub.subscribe(channel)
                print(f"Subscribed to channel {channel}")
                
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        data = json.loads(message['data'])
                        res["data"] = data
                        res["status"] = True
                        res["message"] = f"Received message from channel {channel}: {data}"
                        if callback:
                            callback(data)
                return res
            except redis.RedisError as e:
                print("Error receiving message from Redis:", str(e))
                return res
        else:
            print("Redis instance is not available.")
            return res