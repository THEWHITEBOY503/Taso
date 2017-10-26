import asyncio
import config
import discord
import uvloop
from models import *

party = "🎉"

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

client = discord.Client()

async def mxp(level):
    return (45 + (5 * level))

async def diff(level):
    return max(0, (5 * (level - 30)))

async def levelup(level, exp):
    req = ((8 * level) + await diff(level)) * await mxp(level)
    newexp = exp + await mxp(level)

    if newexp >= req:
        newexp = newexp - req
        newlvl = level + 1

        return newlvl, newexp

    return level, newexp

lock = asyncio.Lock()

@client.event
async def on_message(message):
    lmsg = None
    smsg = None
    async with lock:
        if not message.author.bot:
            server, created = Server.get_or_create(
                    sid=message.server.id)
            user, created = User.get_or_create(
                    uid=message.author.id)
            local, created = LocalLevel.get_or_create(
                    user=user,
                    server=server)

            if message.content.startswith('level.'):
                # Command
                if message.author.server_permissions.manage_server:
                    splitmsg = message.content.split('.')
                    if splitmsg[1] == 'announce':
                        server.announce_channel = message.channel.id


            level, exp = await levelup(
                    server.level,
                    server.experience)
            try:
                if level > server.level:
                    # Yay, the server leveled up
                    if server.announce_channel:
                        channel = client.get_channel(
                                f'{server.announce_channel}')
                        smsg = await client.send_message(channel,
                                f"{party} {message.server.name} is now level {level}! {party}")
            except Exception as e:
                pass

            server.level = level
            server.experience = exp
            server.save()

            level, exp = await levelup(
                    user.level,
                    user.experience)

            user.level = level
            user.experience = exp
            user.save()

            level, exp = await levelup(
                    local.level,
                    local.experience)
            try:
                if level > local.level:
                    # User leveled up on the server
                    lmsg = await client.send_message(message.channel,
                            f"{party} {message.author.name}, you have leveled up to level {level} on {message.server.name}!! {party}")
            except Exception as e:
                pass

            local.level = level
            local.experience = exp
            local.save()

    await asyncio.sleep(10)
    if lmsg:
        await client.delete_message(lmsg)
    if smsg:
        await client.delete_message(smsg)

cfg = config.botConfig()
client.run(cfg.token)
