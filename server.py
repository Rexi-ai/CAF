import asyncio
import json
import os
import time
import uuid
import websockets

ACCESS_KEY = os.environ["ACCESS_KEY"]

ISLEM_OMRU = 150

pcs = {}
botlar = set()
bekleyen = {}


async def botlara_gonder(veri):
    for ws in list(botlar):
        try:
            await ws.send(json.dumps(veri))
        except Exception:
            botlar.discard(ws)


async def bota_gonder(ws, veri):
    try:
        await ws.send(json.dumps(veri))
    except Exception:
        botlar.discard(ws)


async def hata_reply(ws, ref, mesaj):
    await bota_gonder(ws, {"type": "reply", "ref": ref, "ok": False, "error": mesaj})


async def yonlendir(bot_ws, veri):
    tur = veri.get("type")
    hedef = veri.get("name")
    ref = veri.get("ref")

    if not hedef:
        return await hata_reply(bot_ws, ref, "hedef bilgisayar belirtilmedi")

    hedef_ws = pcs.get(hedef)
    if hedef_ws is None:
        return await hata_reply(bot_ws, ref, "bilgisayar bağlı değil")

    paket = dict(veri)
    anahtar = None

    if ref:
        anahtar = uuid.uuid4().hex[:8] + ":" + ref
        bekleyen[anahtar] = {"bot": bot_ws, "pc": hedef,
                             "ref": ref, "zaman": time.time()}
        paket["ref"] = anahtar

    try:
        await hedef_ws.send(json.dumps(paket))
    except Exception:
        if anahtar:
            bekleyen.pop(anahtar, None)
        return await hata_reply(bot_ws, ref, "bilgisayara gönderilemedi")

    if tur == "photo_request":
        await bota_gonder(bot_ws, {"type": "photo_sent", "name": hedef})
    elif tur == "site_request":
        await bota_gonder(bot_ws, {"type": "site_sent", "name": hedef})


async def cevabi_ilet(veri):
    kayit = bekleyen.pop(veri.get("ref"), None)
    if not kayit:
        return

    paket = dict(veri)
    paket["ref"] = kayit["ref"]

    try:
        await kayit["bot"].send(json.dumps(paket))
    except Exception:
        botlar.discard(kayit["bot"])


async def bekleyenleri_temizle():
    while True:
        await asyncio.sleep(30)
        son = time.time()
        for anahtar, kayit in list(bekleyen.items()):
            if son - kayit["zaman"] > ISLEM_OMRU:
                bekleyen.pop(anahtar, None)


async def pc_dustu(pc_adi):
    for anahtar, kayit in list(bekleyen.items()):
        if kayit["pc"] == pc_adi:
            bekleyen.pop(anahtar, None)
            await hata_reply(kayit["bot"], kayit["ref"], "bilgisayar bağlantısı koptu")


async def baglanti(ws):
    rol = None
    pc_adi = None

    try:
        ilk_mesaj = json.loads(await ws.recv())

        if ilk_mesaj.get("key") != ACCESS_KEY:
            await ws.close()
            return

        rol = ilk_mesaj.get("role")

        if rol == "bot":
            botlar.add(ws)
            await ws.send(json.dumps({"type": "connected"}))
            for ad in list(pcs):
                await ws.send(json.dumps({"type": "pc_online", "name": ad}))

            async for mesaj in ws:
                try:
                    veri = json.loads(mesaj)
                except Exception:
                    continue

                tur = veri.get("type")

                if tur == "ping":
                    await ws.send(json.dumps({"type": "pong"}))
                    continue

                if tur == "get_status":
                    await ws.send(json.dumps({
                        "type": "status",
                        "request_id": veri.get("request_id"),
                        "pcs": list(pcs.keys())
                    }))
                else:
                    await yonlendir(ws, veri)

        elif rol == "pc":
            pc_adi = ilk_mesaj.get("name")

            if not pc_adi:
                return

            eski = pcs.get(pc_adi)
            if eski and eski is not ws:
                try:
                    await eski.send(json.dumps({"type": "kicked"}))
                except Exception:
                    pass
                await eski.close()

            pcs[pc_adi] = ws
            await ws.send(json.dumps({"type": "registered"}))
            await botlara_gonder({"type": "pc_online", "name": pc_adi})

            async for mesaj in ws:
                try:
                    veri = json.loads(mesaj)
                except Exception:
                    continue
                tur = veri.get("type")
                if tur == "ping":
                    await ws.send(json.dumps({"type": "pong"}))
                elif tur == "reply":
                    await cevabi_ilet(veri)

    except websockets.ConnectionClosed:
        pass
    except Exception as e:
        print("Hata:", e)

    finally:
        if rol == "pc" and pc_adi and pcs.get(pc_adi) is ws:
            pcs.pop(pc_adi, None)
            await pc_dustu(pc_adi)
            await botlara_gonder({"type": "pc_offline", "name": pc_adi})

        if rol == "bot":
            botlar.discard(ws)


async def main():
    port = int(os.environ.get("PORT", 10000))

    asyncio.create_task(bekleyenleri_temizle())

    async with websockets.serve(
        baglanti, "0.0.0.0", port,
        ping_interval=10, ping_timeout=10,
        max_size=24 * 1024 * 1024
    ):
        print("Sunucu aktif!")
        await asyncio.Future()

asyncio.run(main())
