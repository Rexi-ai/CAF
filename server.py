import asyncio
import os
import json
import websockets

clients = set()
bot_connection = None

async def baglanti(ws):
    global bot_connection

    try:
        async for mesaj in ws:
            veri = json.loads(mesaj)

            if veri.get("type") == "bot":
                bot_connection = ws
                await ws.send(json.dumps({
                    "type": "connected"
                }))

            elif veri.get("type") == "pc":
                for client in list(clients):
                    if client == ws:
                        continue

                if bot_connection:
                    await bot_connection.send(json.dumps(veri))

    except websockets.ConnectionClosed:
        pass
    finally:
        clients.discard(ws)
        if bot_connection == ws:
            bot_connection = None

async def main():
    port = int(os.environ.get("PORT", 10000))

    async with websockets.serve(baglanti, "0.0.0.0", port):
        print("Sunucu aktif!")
        await asyncio.Future()

asyncio.run(main())
