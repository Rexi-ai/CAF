import asyncio
import json
import os
import websockets

ACCESS_KEY = os.environ["ACCESS_KEY"]

pcs = {}
bot_connection = None


async def bot_gonder(veri):
    global bot_connection

    if bot_connection:
        try:
            await bot_connection.send(json.dumps(veri))
        except:
            bot_connection = None


@bot.command()
async def mfoto(ctx, pc_adi: str):
    if not ctx.message.attachments:
        await ctx.send("Fotoğrafı komuta eklemelisin.")
        return

    if not render_ready.is_set() or render_ws is None:
        await ctx.send("Sunucu bağlantısı yok.")
        return

    dosya = ctx.message.attachments[0]

    if not dosya.content_type or not dosya.content_type.startswith("image/"):
        await ctx.send("Bu bir fotoğraf dosyası değil.")
        return

    if pc_adi not in bagli_pc:
        await ctx.send("Bu bilgisayar bağlı değil.")
        return

    fotograf = await dosya.read()

    await render_ws.send(json.dumps({
        "type": "photo_request",
        "name": pc_adi,
        "filename": dosya.filename,
        "image": fotograf.hex()
    }))

    await ctx.send(f"📨 Fotoğraf isteği **{pc_adi}** bilgisayarına gönderildi.")
    
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
