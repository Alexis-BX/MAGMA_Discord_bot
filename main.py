from bot import Bot
from config import *

client = Bot(local_magma = LOCAL_MAGMA)

@client.event
async def on_ready():
    client.ready()

@client.event
async def on_message(message):
    # print(message.content)

    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await client.message_hello(message)

    if message.content.startswith('$run'):
        await client.message_run(message)

    if message.content.startswith('$save'):
        await client.message_save(message)

    if message.content.startswith('$eval'):
        await client.message_eval(message)
        
    # help
    # save stamp

# @client.event
# async def on_message_edit(before, after):
#     print('EDIT')

# @client.event
# async def on_reaction_add(reaction, user):
#     print('REACTION')

@client.event
async def on_raw_reaction_add(payload):
    await client.react_add(payload)

@client.event
async def on_raw_reaction_remove(payload):
    await client.react_rm(payload)

if __name__ == '__main__':
    client.run(TOKEN)
