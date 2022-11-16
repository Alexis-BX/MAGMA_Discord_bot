import discord
import validators
import numpy as np
import pandas as pd
import api as ElutherAI
import random
import asyncio
import time
from ast import literal_eval
import requests

REACTIONS = ['👍','👎','🤷']

def to_list(x):
    return literal_eval(x)

class Bot(discord.Client):
    def __init__(self, local_magma=True):
        self.local_magma = local_magma

        intents = discord.Intents.default()
        intents.reactions = True
        intents.message_content = True
        super(Bot, self).__init__(intents=intents)

        converters = {
            'Answer Magma ethic users': to_list,
            'Answer Magma non-ethic users': to_list,
            'Answer Magma unclear users': to_list
        }

        self.examples = pd.read_csv('data/data.csv', converters=converters)

        self.eval_messages_line = {}

        self.images = []

        try:
            for line in open('data/images.txt').readlines():
                line = line.strip()
                if len(line)>0 and validators.url(line):
                    self.images.append(line)
        except FileNotFoundError:
            pass

        self.images_messages = {}

        if self.local_magma:
            from magma_local_run import Magma
            self.magma = Magma()

    def run_magma(self, img_url, img_prompt):
        img_prompt = img_prompt.strip()

        img_prompt = img_prompt.replace('\\n', '\n')

        if img_prompt[-2:] == 'A:':
            img_prompt = img_prompt[:-2].strip()
            img_prompt = img_prompt + '\nA:'

        img_prompt = img_prompt + ' '

        if self.local_magma:
            print(img_prompt)
            output = self.magma.run(img_url, img_prompt)
            print(output)
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
        await message.channel.send('Hello!', reference=message)

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
        await message.channel.send('\n'.join(commands), reference=message)

    async def message_run(self, message):
        img_url, img_prompt = '', ''
        lines = message.content.split('\n')

        if len(lines) < 2:
            await message.channel.send('Improper formatting.\nProper format:\n$run\nURL: https://...\nprompt: This is a picture of', reference=message)
            return
        
        line = lines[1].strip()
        if line[:4].lower() == 'url:':
            line = line[4:]
        img_url = line.strip()
        
        line = '\n'.join(lines[2:])
        line = line.strip()
        if line[:7].lower() == 'prompt:':
            line = line[7:]
        img_prompt = line.strip()
            
        if len(img_prompt)==0 or len(img_url)==0 or not validators.url(img_url):
            await message.channel.send('Improper formatting.\nProper format:\n$run\nURL: https://...\nprompt: This is a picture of', reference=message)
            return

        if not validators.url(img_url) or requests.get(img_url).status_code != 200:
            await message.channel.send('Invalid URL', reference=message)
            return


        await message.channel.send('Running...', reference=message)

        img_ans = self.run_magma(img_url, img_prompt)

        eval_msg = await message.channel.send('**' + img_ans + '**', reference=message)
    
        for react in REACTIONS:
            await eval_msg.add_reaction(react)
        
        line_num = self.add_line(img_url, img_prompt, img_ans)
        self.eval_messages_line[eval_msg.id] = line_num
                
    async def message_eval_single(self, message, line_num):
        line = self.examples.loc[line_num]
        img_url = line['Image URL']
        img_prompt = line['Prompt']

        if line['Answer Magma']==pd.notna or len(line['Answer Magma'].strip())==0:
            img_ans = self.run_magma(img_url, img_prompt)
            self.examples.at[line_num, 'Answer Magma'] = img_ans
        else:
            img_ans = line['Answer Magma']
            
        eval_msg = await message.channel.send(img_url + '\n' + img_prompt + ' **' + img_ans + '**', reference=message)
    
        for react in REACTIONS:
            await eval_msg.add_reaction(react)

        self.eval_messages_line[eval_msg.id] = line_num

    async def message_eval(self, message):
        await message.channel.send('Finding a message to evaluate.', reference=message)

        msg = message.content.strip().split(' ')
        msg = [x for x in msg if x] # remove empty strings
        if len(msg) > 1:
            amount = int(msg[1])
        else:
            amount = 1
        
        N = self.examples.shape[0]-1
        line_num = random.randint(0, N)

        for i in range(line_num, line_num+amount):
            await self.message_eval_single(message, i % N)
        
    async def message_save(self, message):
        self.examples.to_csv('data/data_' + str(time.time_ns()) + '.csv', index=False)

        file = open('data/images_' + str(time.time_ns()) + '.txt', 'w')
        file.write('\n'.join(self.images))
        file.flush()
        file.close()
        
        await message.channel.send('Table saved!', reference=message)

    async def message_img(self, message):
        urls = message.content.strip().split()[1:]
        for url in urls:
            url = url.strip()
            if validators.url(url) and requests.get(url).status_code == 200:
                self.images.append(url)
        await message.channel.send("Thank you for the images!", reference=message)

    async def message_prompt_single(self, message):
        if len(self.images) > 0:
            img_url = self.images.pop()
        else:
            line_num = random.randint(0, self.examples.shape[0]-1)
            line = self.examples.loc[line_num]
            img_url = line['Image URL']
        
        msg = await message.channel.send(img_url, reference=message)
        self.images_messages[msg.id] = img_url

    async def message_prompt(self, message):
        msg = message.content.strip().split(' ')
        msg = [x for x in msg if x] # remove empty strings
        if len(msg) > 1:
            amount = int(msg[1])
        else:
            amount = 1

        for _ in range(amount):
            await self.message_prompt_single(message)

    async def message_prompt_followup(self, message):
        if message.reference.resolved.id not in self.images_messages.keys():
            return

        img_url = self.images_messages[message.reference.resolved.id]
        img_prompt = message.content.strip()
        if len(img_prompt) < 1:
            return

        img_ans = self.run_magma(img_url, img_prompt)

        eval_msg = await message.channel.send('**' + img_ans + '**', reference=message)
        
        for react in REACTIONS:
            await eval_msg.add_reaction(react)

        line_num = self.add_line(img_url, img_prompt, img_ans)
        self.eval_messages_line[eval_msg.id] = line_num
        
    async def react_add(self, payload):
        if payload.user_id == self.user:
            return
        if not payload.emoji.is_unicode_emoji():
            return
        if payload.message_id not in self.eval_messages_line.keys():
            return

        react = payload.emoji.name
        line_num = self.eval_messages_line[payload.message_id]
        react_text = ''
        if react == '👍':
            react_text = 'ethic'
        elif react == '👎':
            react_text = 'non-ethic'
        elif react == '🤷':
            react_text = 'unclear'
        else:
            print(payload.emoji.name + ' not in accepted reactions')
            return
        
        if payload.user_id not in self.examples['Answer Magma ' + react_text + ' users'][line_num]:
            self.examples['Answer Magma ' + react_text + ' users'][line_num].append(payload.user_id)
            self.examples.at[line_num, 'Answer Magma ' + react_text] += 1

    async def react_rm(self, payload):
        if payload.user_id == self.user:
            return
        if not payload.emoji.is_unicode_emoji():
            return
        if payload.message_id not in self.eval_messages_line.keys():
            return

        react = payload.emoji.name
        line_num = self.eval_messages_line[payload.message_id]
        react_text = ''
        if react == '👍':
            react_text = 'ethic'
        elif react == '👎':
            react_text = 'non-ethic'
        elif react == '🤷':
            react_text = 'unclear'
        else:
            print(payload.emoji.name + ' not in accepted reactions')
            return
        
        if payload.user_id not in self.examples['Answer Magma ' + react_text + ' users'][line_num]:
            self.examples['Answer Magma ' + react_text + ' users'][line_num].remove(payload.user_id)
            self.examples.at[line_num, 'Answer Magma ' + react_text] -= 1
            
            
    def add_line(self, img_url, img_prompt, img_ans):
        tmp_table = pd.DataFrame.from_dict({
            "Image URL": [img_url],
            "Prompt": [img_prompt],
            "Answer Magma": [img_ans],
            "Answer Magma ethic": [0],
            "Answer Magma ethic users": [[]],
            "Answer Magma non-ethic": [0],
            "Answer Magma non-ethic users": [[]],
            "Answer Magma unclear": [0],
            "Answer Magma unclear users": [[]]
        })
        self.examples = pd.concat([self.examples, tmp_table], ignore_index=True, copy=False)
        return self.examples.shape[0] - 1