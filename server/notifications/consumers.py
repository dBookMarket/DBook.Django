from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'notification_{self.user_id}'

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
