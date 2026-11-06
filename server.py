
import asyncio
import os
import websockets

async def baglanti(websocket):
    print("Yeni bilgisayar bağlandı!")

    try:
        async for mesaj in websocket:
            print("Gelen mesaj:", mesaj)
            await websocket.send("SUNUCU_OK")

    except websockets.ConnectionClosed:
        print("Bağlantı kesildi.")

async def main():
    port = int(os.environ.get("PORT", 10000))

    async with websockets.serve(baglanti, "0.0.0.0", port):
        print("WebSocket sunucusu aktif!")
        await asyncio.Future()

asyncio.run(main())
