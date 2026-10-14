"""Your first RoomKit conversation, using a scripted AI reply.

Requires Python 3.12+ and `pip install roomkit`.
Run with `python first_conversation.py`. No API key or network service is used.
Replace MockAIProvider with a real provider when you're ready.
"""

import asyncio

from roomkit import AIChannel, InboundMessage, RoomKit, TextContent, WebSocketChannel
from roomkit.providers.ai.mock import MockAIProvider


async def main():
    async with RoomKit() as kit:
        ai = AIChannel(
            "assistant",
            provider=MockAIProvider(
                responses=["Hello from your first room."]
            ),
        )
        kit.register_channel(WebSocketChannel("chat"))
        kit.register_channel(ai)
        room = await kit.create_room()
        await kit.attach_channel(room.id, "chat")
        await kit.attach_channel(room.id, "assistant")

        await kit.process_inbound(InboundMessage(
            channel_id="chat",
            sender_id="you",
            content=TextContent(body="Hello, RoomKit!"),
        ))
        for event in await kit.store.list_events(room.id):
            if isinstance(event.content, TextContent):
                print(f"{event.source.channel_id}: {event.content.body}")


if __name__ == "__main__":
    asyncio.run(main())
