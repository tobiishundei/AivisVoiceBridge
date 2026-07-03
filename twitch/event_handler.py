class EventHandler:

    async def on_connect(self, session_id: str):

        print()
        print("===================================")
        print("WebSocket Connected")
        print()
        print("Session ID:")
        print(session_id)