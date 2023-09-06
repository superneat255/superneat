import os
import json
import asyncio
import requests
from os import remove
from PIL import Image
from shlex import split
from subprocess import run
from os.path import basenam
from urllib.parse import urlparse, unquote
from helpers import b64_decode, b64_encode

try:
    from FastTelethon import upload_file
except:
    run(split("sudo pip install telethon"))
    from FastTelethon import upload_file

from telethon import utils
from telethon.tl import types
from telethon.sync import TelegramClient



class UploadTelegram(object):
    """Made with love by Immanuel Pishon Mwananjela (Superneat)"""
    """superneat2013@gmail.com"""


    def __init__(
        self, 
        api_id,
        api_hash,
        bot_token,
        session=None,
        debug=False
    ):
        super(UploadTelegram, self).__init__()
        
        self.api_id    = api_id
        self.api_hash  = api_hash
        self.bot_token = bot_token
        self.session   = session
        self.debug     = debug

        if not self.session: self.session=self.bot_token.split(':')[0]


    def log(self, s):
        if not self.debug: return
        print()
        try:
            print( json.dumps(s, indent=4) if isinstance(s, dict) or isinstance(s, list) else s )
        except: print(s)
        print('--------------------------------------')


    def filename_from_url(self, url):
        return unquote(basename(urlparse(url).path))


    async def download_from_url(self, download_url, filename):
        file_download = requests.get(download_url, stream=True)
        with open(filename, 'wb') as f:
            for chunk in file_download.iter_content(chunk_size=256*1024*2):
                if chunk:
                    f.write(chunk)
                    f.flush()
        return filename
    

    async def upload_file2(self, download_url):
        path = None
        file_name = self.filename_from_url(download_url)

        if '.heic' in file_name:
            path = await self.download_from_url(download_url, file_name)
            
            image = Image.open(path)

            file_name = file_name.replace('.heic', '.jpg')
            image.convert('RGB').save(file_name)
            
            # file_name = file_name.replace('.heic', '.png')
            # image.save(file_name)

            with open(path, "rb") as out:
                result = await upload_file(self.client, out, filename=file_name)

            if path: remove(path)

        else:
            file_download = requests.get(download_url, stream=True)
            for chunk in file_download.iter_content(chunk_size=256*1024*2):
                if chunk:
                    result = await self.client.upload_file(chunk, part_size_kb=512, file_name=file_name)
            
        return result


    async def SendMessage(self, obj):
        parse_mode = 'HTML' if 'parse_mode' not in obj else obj['parse_mode']
        await self.client.send_message(
            int(obj['chat_id']), 
            obj['text'], 
            parse_mode=parse_mode, 
            link_preview=False)


    async def SendMediaGroup(self, obj):
        parse_mode = 'HTML' if 'parse_mode' not in obj else obj['parse_mode']

        album = []
        for file_url in obj['album']:
            file = await self.upload_file2(file_url)
            album.append(file)

        if obj['caption']['limit_exceeded']:
            await self.client.send_file(int(obj['chat_id']), album, caption=obj['caption2'], parse_mode=parse_mode)
            await self.SendMessage({'chat_id':obj['chat_id'], 'text':obj['caption']['caption']})
        else:
            await self.client.send_file(int(obj['chat_id']), album, caption=obj['caption']['caption'], parse_mode=parse_mode)


    async def SendVideo(self, obj):
        try:
            parse_mode = 'HTML' if 'parse_mode' not in obj else obj['parse_mode']

            #Download video
            filename = self.filename_from_url(obj['url'])
            if 'http' in obj['url']: path = await self.download_from_url(obj['url'], filename)
            else: path = obj['url']

            async with self.client.action(obj['chat_id'], 'document') as action:
                with open(path, "rb") as out:
                    res = await upload_file(self.client, out, filename=filename)

                    if 'thumb' in obj: thumb = await self.download_from_url(obj['thumb'], 'thumb.jpg')
                    else: thumb = ''
                    
                    attributes, mime_type = utils.get_attributes(path)

                    attributes[1].w = 720 if attributes[1].w < 10 else attributes[1].w
                    attributes[1].h = 480 if attributes[1].h < 10 else attributes[1].h
                    attributes[1].supports_streaming = True

                    if obj['caption']['limit_exceeded']:
                        await self.client.send_file(
                            int(obj['chat_id']), 
                            file=res, 
                            caption=obj['caption2'],
                            parse_mode=parse_mode,
                            thumb=thumb,
                            attributes=attributes
                        )
                        await self.SendMessage({'chat_id':obj['chat_id'], 'text':obj['caption']['caption']})
                    else:
                        await self.client.send_file(
                            int(obj['chat_id']),
                            file=res, 
                            caption=obj['caption']['caption'],
                            parse_mode=parse_mode,
                            thumb=thumb,
                            attributes=attributes
                        )

            remove(path)
        except Exception as e:
            self.log(e)


    async def SendPhoto(self, obj):
        parse_mode = 'HTML' if 'parse_mode' not in obj else obj['parse_mode']
        file = await self.upload_file2(obj['url'])
        
        if obj['caption']['limit_exceeded']:
            await self.client.send_file(int(obj['chat_id']), file, caption=obj['caption2'], parse_mode=parse_mode)
            await self.SendMessage({'chat_id':int(obj['chat_id']), 'text':obj['caption']['caption']})
        else:
            await self.client.send_file(int(obj['chat_id']), file, caption=obj['caption']['caption'], parse_mode=parse_mode)


    async def execute(self, method, argv):
        try:
            self.client = await TelegramClient(
                            self.session, 
                            self.api_id, 
                            self.api_hash).start(bot_token=self.bot_token)
        except:
            remove(f'{self.session}.session')
            self.client = await TelegramClient(
                            self.session, 
                            self.api_id, 
                            self.api_hash).start(bot_token=self.bot_token)

        async with self.client:
            obj = json.loads(b64_decode(argv))

            try:
                await getattr(self, method)(obj)
            except Exception as e:
                self.log(e)
                await self.SendMessage({
                    'chat_id':obj['chat_id'], 
                    'text':f'Unknown error occurred: {e}'
                })



if __name__ == '__main__':
    async def main():
        api_id    = 1194030
        api_hash  = '54478ce7218680737bcf594aec08f298'
        bot_token = '6042990289:AAGJlDmbZGkyxWMnvr9BGquyFjvEeMYaf_Q'
        
        ut = UploadTelegram(
                api_id=api_id,
                api_hash=api_hash,
                bot_token=bot_token,
                debug=True
            )
        await ut.execute('SendMessage', b64_encode(json.dumps({
            'chat_id':392040958, 
            'text':'Just testing!'
        })))

        await ut.execute('SendVideo', b64_encode(json.dumps({
            'chat_id':392040958, 
            'url':'https://superneatech.com/telegram/bots/teleploadbot/lib/@bongohits_group.Trailer.Pathaan.2023.mp4', 
            'caption':{'caption':'Just testing!', 'limit_exceeded':False},
            'thumb': 'https://superneatech.com/telegram/bots/teleploadbot/thumb.jpg'
        })))

    asyncio.run(main())
