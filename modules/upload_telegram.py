import os
import json
import requests
from os import remove
from PIL import Image
from os.path import basename
from FastTelethon import upload_file
from urllib.parse import urlparse, unquote
from helpers import b64_decode, b64_encode

try:
  from telethon import utils
except:
  os.system('pip install telethon')
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
            path = await self.download_from_url(obj['url'], filename)

            with open(path, "rb") as out:
                res = await self.upload_file(self.client, out, filename=filename)

                attributes, mime_type = utils.get_attributes(path)

                attributes[1].w = 720 if attributes[1].w < 10 else attributes[1].w
                attributes[1].h = 480 if attributes[1].h < 10 else attributes[1].h
                attributes[1].supports_streaming = True

                media = types.InputMediaUploadedDocument(
                    file       = res,
                    mime_type  = mime_type,
                    force_file = False,
                    attributes=attributes
                )

                if obj['caption']['limit_exceeded']:
                    await self.client.send_file(
                        int(obj['chat_id']), 
                        file=media, 
                        caption=obj['caption2'],
                        parse_mode=parse_mode
                    )
                    await self.SendMessage({'chat_id':obj['chat_id'], 'text':obj['caption']['caption']})
                else:
                    await self.client.send_file(
                        int(obj['chat_id']),
                        file=media, 
                        caption=obj['caption']['caption'],
                        parse_mode=parse_mode
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


    def execute(self, method, argv):
        self.client = TelegramClient(
                        self.session, 
                        self.api_id, 
                        self.api_hash).start(bot_token=self.bot_token)

        with self.client:
            obj = json.loads(b64_decode(argv))

            try:
                self.client.loop.run_until_complete( getattr(self, method)(obj) )
            except Exception as e:
                self.log(e)
                self.client.loop.run_until_complete(self.SendMessage({
                    'chat_id':obj['chat_id'], 
                    'text':f'Unknown error occurred: {e}'
                }) )



if __name__ == '__main__':
    ut = UploadTelegram(
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            debug=True
        )
    ut.execute('SendMessage', b64_encode(json.dumps({
        'chat_id':392040958, 
        'text':'Just testing!'
    })))
