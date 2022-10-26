import discord
import validators
import numpy as np
import pandas as pd
import api as ElutherAI
import random
import asyncio
import time

REACTIONS = ['👍','👎','🤷']

class Bot(discord.Client):
    def __init__(self, local_magma=True):
        self.local_magma = local_magma

        intents = discord.Intents.default()
        intents.reactions = True
        intents.message_content = True
        super(Bot, self).__init__(intents=intents)

        self.examples = pd.read_csv('data/initial_30.csv')

        self.reactions = {react:i for i, react in enumerate(REACTIONS)} 
        self.eval_messages = {}
        self.eval_messages_users = {}

        self.images = []
        self.images_messages = {}

        if self.local_magma:
            from magma_local_run import Magma
            self.magma = Magma()

    def run_magma(self, img_url, img_prompt):
        if self.local_magma:
            output = self.magma.run(img_url, img_prompt)
        else:
            output = ElutherAI.predict_single(img_url, img_prompt)
        
        return output[0]

    def ready(self):
        print('We have logged in as {0.user}'.format(self))

    ### Message handling
    async def message_handle_all(self, message):
        # print(message)
        # print(message.type)
        # print(message.reference)
        # print(message.content)
        # print(message.reference.resolved)

        if message.author == self.user:
            return

        elif message.content.startswith('$hello'):
            await self.message_hello(message)

        elif message.content.startswith('$help'):
            await self.message_help(message)

        elif message.content.startswith('$run'):
            await self.message_run(message)

        elif message.content.startswith('$eval'):
            await self.message_eval(message)

        elif message.content.startswith('$save'):
            await self.message_save(message)
        
        elif message.content.startswith('$image'):
            await self.message_img(message)

        elif message.content.startswith('$prompt'):
            await self.message_prompt(message)

        elif message.type == discord.MessageType.reply:
            await self.message_prompt_followup(message)

    async def message_hello(self, message):
        await message.channel.send('Hello!')

    async def message_help(self, message):
        commands = [
            "Possible commands:",
            "$hello   ping bot to ensure proper function",
            "$help    list available actions",
            "$run     run MAGMA with a image and prompt",
            "$eval    get a MAGMA answer to evaluate",
            "$save    save the current answer table",
            "$image   space seperated list of image URLs",
            "$prompt  get an image for which to write a prompt"
        ]
        await message.channel.send('\n'.join(commands))

    async def message_run(self, message):
        await message.channel.send('Running...')

        img_url, img_prompt = '', ''
        for line in message.content.split('\n'):
            if len(line.split(':')) < 2:
                continue

            line = line.strip()

            if line[:4].lower() == 'url:':
                img_url = line[4:].strip()
            if line[:7].lower() == 'prompt:':
                img_prompt = line[7:].strip()
            
        if len(img_prompt)==0 or len(img_url)==0:
            await message.channel.send('Improper formatting.\nProper format:\n$run\nURL: https://...\nprompt: This is a picture of')
            return

        img_ans = self.run_magma(img_url, img_prompt)

        eval_msg = await message.channel.send('**' + img_ans + '**')
    
        for react in self.reactions.keys():
            await eval_msg.add_reaction(react)
        self.eval_messages[eval_msg.id] = [0]*len(self.reactions.keys())
        self.eval_messages_users[eval_msg.id] = [[] for _ in range(len(self.reactions.keys()))]
                
        self.add_line(img_url, img_prompt, img_ans)

    async def message_eval(self, message):
        await message.channel.send('Finding a message to evaluate.')

        line_num = random.randint(0, self.examples.shape[0]-1)
        line = self.examples.loc[line_num]
        img_url = line['Image URL']
        img_prompt = line['Prompt']

        if line['Answer Magma']!=pd.notna or len(line['Answer Magma'].strip())==0:
            img_ans = self.run_magma(img_url, img_prompt)
            self.examples.at[line_num, 'Answer Magma'] = img_ans
        else:
            img_ans = line['Answer Magma']
            
        eval_msg = await message.channel.send(img_url + '\n' + img_prompt + ' **' + img_ans + '**')
    
        for react in self.reactions.keys():
            await eval_msg.add_reaction(react)

        self.eval_messages[eval_msg.id] = [0]*len(self.reactions.keys())
        self.eval_messages_users[eval_msg.id] = [[] for _ in range(len(self.reactions.keys()))]

    async def message_save(self, message): 
        self.examples.to_csv('data/initial_30_' + str(time.time_ns()) + '.csv', index=False)
        await message.channel.send('Table saved!')

    async def message_img(self, message):
        urls = message.content.strip().split()[1:]
        for url in urls:
            url = url.strip()
            if validators.url(url):
                self.images.append(url)
        await message.channel.send("Thank you for the images!")

    async def message_prompt(self, message):
        if len(self.images) > 0:
            img_url = self.images[-1]
        else:
            line_num = random.randint(0, self.examples.shape[0]-1)
            line = self.examples.loc[line_num]
            img_url = line['Image URL']
        
        msg = await message.channel.send(img_url, reference=message)
        self.images_messages[msg.id] = img_url

    async def message_prompt_followup(self, message):
        if message.reference.resolved.id not in self.images_messages.keys():
            return

        img_url = self.images_messages[message.reference.resolved.id]
        img_prompt = message.content.strip()
        if len(img_prompt) < 1:
            return

        img_ans = self.run_magma(img_url, img_prompt)

        eval_msg = await message.channel.send('**' + img_ans + '**', reference=message)
        
        for react in self.reactions.keys():
            await eval_msg.add_reaction(react)
        self.eval_messages[eval_msg.id] = [0]*len(self.reactions.keys())
        self.eval_messages_users[eval_msg.id] = [[] for _ in range(len(self.reactions.keys()))]

        print(self.examples.shape)   
        self.add_line(img_url, img_prompt, img_ans)
        print(self.examples.shape)   
        print(self.examples.tail)   

    async def react_add(self, payload):
        if payload.user_id == self.user:
            return
        if not payload.emoji.is_unicode_emoji():
            return
        if payload.message_id not in self.eval_messages.keys():
            return

        try:
            i = self.reactions[payload.emoji.name]
            self.eval_messages[payload.message_id][i] += 1
            self.eval_messages_users[payload.message_id][i].append(payload.user_id)
        except KeyError:
            print(payload.emoji.name + ' not in reactions')
            return
            
        print(self.eval_messages[payload.message_id])
        print(self.eval_messages_users[payload.message_id])

    async def react_rm(self, payload):
        if payload.user_id == self.user:
            return
        if not payload.emoji.is_unicode_emoji():
            return
        if payload.message_id not in self.eval_messages.keys():
            return

        try:
            i = self.reactions[payload.emoji.name]
            self.eval_messages[payload.message_id][i] -= 1
            self.eval_messages_users[payload.message_id][i].remove(payload.user_id)
        except KeyError:
            print(payload.emoji.name + ' not in reactions')
            return
            
        print(self.eval_messages[payload.message_id])
        print(self.eval_messages_users[payload.message_id])

    def add_line(self, img_url, img_prompt, img_ans):
        tmp_table = pd.DataFrame.from_dict({
            "Image URL": [img_url],
            "Prompt": [img_prompt],
            "Answer Magma": [img_ans],
        })
        self.examples = pd.concat([self.examples, tmp_table], ignore_index=True, copy=False)
        