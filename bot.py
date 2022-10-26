import discord
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

        if self.local_magma:
            from magma_local_run import Magma
            self.magma = Magma()

    def run_magma(self, img_url, img_prompt):
        if self.local_magma:
            output = self.magma(img_url, img_prompt)
        else:
            output = ElutherAI.predict_single(img_url, img_prompt)
        
        return output

    def ready(self):
        print('We have logged in as {0.user}'.format(self))

    async def message_run(self, message):
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

        img_ans, duration, avg = self.run_magma(img_url, img_prompt)

        eval_msg = await message.channel.send('**' + img_ans + '**')
    
        for react in self.reactions.keys():
            await eval_msg.add_reaction(react)
        self.eval_messages[eval_msg.id] = [0]*len(self.reactions.keys())
        self.eval_messages_users[eval_msg.id] = [[] for _ in range(len(self.reactions.keys()))]
                
        self.examples.append({'Image URL':img_url, 'Prompt':img_prompt, 'Answer Magma':img_ans}, ignore_index=True)

    async def message_save(self, message): 
        self.examples.to_csv('data/initial_30_' + str(time.time_ns()) + '.csv', index=False)

    async def message_hello(self, message):
        await message.channel.send('Hello!')

    async def message_eval(self, message): 
        line_num = random.randint(0, self.examples.shape[0]-1)
        line = self.examples.loc[line_num]
        img_url = line['Image URL']
        img_prompt = line['Prompt']

        if line['Answer Magma']!=pd.notna or len(line['Answer Magma'].strip())==0:
            img_ans, _, _ = self.run_magma(img_url, img_prompt)
            self.examples.at[line_num, 'Answer Magma'] = img_ans
        else:
            img_ans = line['Answer Magma']
            
        eval_msg = await message.channel.send(img_url + '\n' + img_prompt + ' **' + img_ans + '**')
    
        for react in self.reactions.keys():
            await eval_msg.add_reaction(react)

        self.eval_messages[eval_msg.id] = [0]*len(self.reactions.keys())
        self.eval_messages_users[eval_msg.id] = [[] for _ in range(len(self.reactions.keys()))]

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

