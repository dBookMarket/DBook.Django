from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework.authtoken.models import Token
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncJsonWebsocketConsumer):

    @database_sync_to_async
    def get_user(self, query_string: str):
        try:
            for param in query_string.split('&'):
                k_v = param.split('=')
                if len(k_v) == 2:
                    if k_v[0] == 'token':
                        token = Token.objects.get(key=k_v[1])
                        return token.user
        except Token.DoesNotExist:
            return None
    
    async def connect(self):
        user = await self.get_user(self.scope['query_string'].decode())
        # user = self.scope['user']

        if user is None or not user.is_authenticated:
            print(f'User {user} is not authenticated.')
            await self.close()

        self.group_name = f'notification_{user.id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.close()

    # Receive message from WebSocket
    async def receive_json(self, content, **kwargs):
        message = content["message"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.group_name, {"type": "notify", "message": message}
        )

    # Receive message from room group
    async def notify(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send_json(content={"message": message})
