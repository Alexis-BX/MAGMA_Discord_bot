from bot import Bot
from config import *

client = Bot(local_magma = LOCAL_MAGMA)

@client.event
async def on_ready():
    client.ready()

@client.event
async def on_message(message):
    await client.message_handle_all(message)

@client.event
async def on_raw_reaction_add(payload):
    await client.react_add(payload)

@client.event
async def on_raw_reaction_remove(payload):
    await client.react_rm(payload)

# @client.event
# async def on_message_edit(before, after):
#     print('EDIT')

# @client.event
# async def on_reaction_add(reaction, user):
#     print('REACTION')

if __name__ == '__main__':
    client.run(TOKEN)
