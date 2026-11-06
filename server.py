import asyncio
import json
import os
import websockets

ACCESS_KEY = os.environ["beGslQVbWstRx6iN"]

pcs = {}
bot_connection = None


async def bot_gonder(veri):
    global bot_connection

    if bot_connection:
        try:
            await bot_connection.send(json.dumps(veri))
        except:
            bot_connection = None


async def baglanti(ws):
    global bot_connection

    rol = None
    pc_adi = None

    try:
        ilk_mesaj = json.loads(await ws.recv())

        if ilk_mesaj.get("key") != ACCESS_KEY:
            await ws.close()
            return

        rol = ilk_mesaj.get("role")

        if rol == "bot":
            bot_connection = ws
            await ws.send(json.dumps({"type": "connected"}))

            async for mesaj in ws:
                veri = json.loads(mesaj)

                if veri.get("type") == "get_status":
                    await ws.send(json.dumps({
                        "type": "status",
                        "request_id": veri.get("request_id"),
                        "pcs": list(pcs.keys())
                    }))

        elif rol == "pc":
            pc_adi = ilk_mesaj.get("name")

            if not pc_adi:
                await ws.close()
                return

            pcs[pc_adi] = ws

            await ws.send(json.dumps({"type": "registered"}))

            await bot_gonder({
                "type": "pc_online",
                "name": pc_adi
            })

            await ws.wait_closed()

    except websockets.ConnectionClosed:
        pass
    except Exception as e:
        print("Hata:", e)

    finally:
        if rol == "pc" and pc_adi and pcs.get(pc_adi) == ws:
            del pcs[pc_adi]

            await bot_gonder({
                "type": "pc_offline",
                "name": pc_adi
            })

        if rol == "bot" and bot_connection == ws:
            bot_connection = None


async def main():
    port = int(os.environ.get("PORT", 10000))

    async with websockets.serve(
        baglanti,
        "0.0.0.0",
        port,
        ping_interval=10,
        ping_timeout=10
    ):
        print("Sunucu aktif!")
        await asyncio.Future()


asyncio.run(main())
