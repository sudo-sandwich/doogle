import aiofiles
import aiohttp
import discord
from discord.ext import tasks
import json
import logging
import time

with open('keys.json', 'r') as f:
    keys = json.load(f)

current_searches = {}

class DoogleClient(discord.Client):
    async def setup_hook(self):
        self.clear_old_searches.start()

    async def on_message(self, message):
        if message.author == client.user:
            return
        if not message.content.startswith(',img '):
            return
        
        query = message.content[5:]
        newMessage = await message.channel.send(embed=discord.Embed(title=f'doogle "{query}"', description='Loading...', color=0x00ff00))
        response = await search_google_images(query, 0, write_file=True)
        #response = await get_test_response()
        current_searches[newMessage.id] = {
            'message': newMessage,
            'current_index': 0,
            'query': query,
            'last_modified': time.time(),
            'items': response['items'],
        }
        await shift_search_result(newMessage.id, 0)

        await newMessage.add_reaction('⏮️')
        await newMessage.add_reaction('◀️')
        await newMessage.add_reaction('▶️')
        await newMessage.add_reaction('⏭️')

    async def on_reaction_add(self, reaction, user):
        if not reaction.message.id in current_searches:
            return
        if user == client.user:
            return
        
        if reaction.emoji == '⏮️':
            await shift_search_result(reaction.message.id, -10)
        elif reaction.emoji == '◀️':
            await shift_search_result(reaction.message.id, -1)
        elif reaction.emoji == '▶️':
            await shift_search_result(reaction.message.id, 1)
        elif reaction.emoji == '⏭️':
            await shift_search_result(reaction.message.id, 10)

        await reaction.remove(user)

    @tasks.loop(seconds=60)
    async def clear_old_searches(self):
        messages_to_remove = []
        for message_id, search in current_searches.items():
            if time.time() - search['last_modified'] > 86400:
                messages_to_remove.append(message_id)
        
        for message_id in messages_to_remove:
            await current_searches[message_id]['message'].clear_reactions()
            del current_searches[message_id]

    @clear_old_searches.before_loop
    async def before_clear_old_searches(self):
        await client.wait_until_ready()

async def search_google_images(query, start_index, write_file=False):
    params = {
        'key': keys['google'],
        'cx': keys['pse_engine_id'],
        'q': query,
        'start': start_index,
        'searchType': 'image'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://customsearch.googleapis.com/customsearch/v1', params=params) as resp:
            resp_json = await resp.json()

            if write_file:
                await save_dict_to_json_file(resp_json, 'response.json')
            
            return resp_json

async def save_dict_to_json_file(data, filename):
    json_string = json.dumps(data, indent=4)
    async with aiofiles.open(filename, 'w') as f:
        await f.write(json_string)

async def get_test_response():
    async with aiofiles.open('response.json', 'r') as f:
        return json.loads(await f.read())
    
async def shift_search_result(message_id, shift_amount):
    index = current_searches[message_id]['current_index'] + shift_amount
    if index < 0:
        index = 0
    
    # get more search results if we need to
    while index >= len(current_searches[message_id]['items']):
        newSearchResponse = await search_google_images(current_searches[message_id]['query'], len(current_searches[message_id]['items']) + 1)
        current_searches[message_id]['items'].extend(newSearchResponse['items'])
    
    embed = create_embed_from_search_result(message_id, index)
    current_searches[message_id]['current_index'] = index
    current_searches[message_id]['last_modified'] = time.time()
    await current_searches[message_id]['message'].edit(embed=embed)
    
def create_embed_from_search_result(message_id, index):
    item = current_searches[message_id]['items'][index]
    embed = discord.Embed(title=f'doogle "{current_searches[message_id]['query']}"', type='rich', color=0x00ff00, description=item['image']['contextLink'])
    embed.set_image(url=item['link'])
    embed.set_footer(text=f'Result {index + 1}')
    return embed

log_handler = logging.FileHandler(filename='doogle.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = DoogleClient(intents=intents)
client.run(keys['discord'], log_handler=log_handler, log_level=logging.DEBUG)