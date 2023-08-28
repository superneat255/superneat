import json
import asyncio
import requests
from os import remove
from shlex import split
from helpers import runSh
from subprocess import run
from os.path import isfile
from urllib.parse import urlparse

try:
    from playwright.async_api import async_playwright
except:
    run(split("sudo pip install playwright"))
    run(split("sudo playwright install"))
    run(split("sudo playwright install-deps"))
    from playwright.async_api import async_playwright




class Drivefire(object):
    """Made with love by Immanuel Pishon Mwananjela (Superneat)"""
    """superneat2013@gmail.com"""
    

    def __init__(self, email=None, passwd=None, debug=True):
        super(Drivefire, self).__init__()
        self.email  = email
        self.passwd = passwd
        self.debug  = debug


    def log(self, s):
        print()
        print( json.dumps(s, indent=4) if isinstance(s, dict) else s )
        print('--------------------------------------')


    async def drivefire_session(self):
        PHPSESSID=''
        if isfile('trash.bin'):
            with open('trash.bin', 'r') as f: PHPSESSID = f.read()
            self.log('Drivefire saved session found...')
            return PHPSESSID

        try:
            if not self.email or not self.passwd: raise
            
            self.log('Drivefire session not found, regenerating...')

            code=''
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=True)
                context = await browser.new_context()

                page = await context.new_page()
                await page.goto('https://drivefire.co/login')

                await page.locator('#identifierId').type(self.email)
                await asyncio.sleep(2)
                await page.locator('#identifierNext > div > button > span').click()
                await asyncio.sleep(5)
                await page.locator("[name='Passwd']").type(self.passwd)
                await asyncio.sleep(2)
                await page.locator('#passwordNext > div > button > span').click()
                await asyncio.sleep(2)
                await page.locator('#submit_approve_access > div > button > span').click()
                
                await asyncio.sleep(5)
                code = page.url

                await page.goto('https://drivefire.co/login2.php')
                await page.locator("[name='fname']").type(code)
                await page.locator("[type='submit']").click()
                await asyncio.sleep(3)
                
                cookies = await context.cookies()
                for cookie in cookies:
                    if cookie['name']=='PHPSESSID':
                        PHPSESSID=cookie['value']
                
                await browser.close()
        except:
            self.log('Failed to get PHPSESSID, input manually!')
            PHPSESSID = input('Input PHPSESSID: ')

        
        if PHPSESSID:
            self.log(f'Got PHPSESSID: {PHPSESSID}')
            with open('trash.bin', 'w') as f: f.write(PHPSESSID)
            return PHPSESSID


    async def drivefire(self, url, retries=0):
        PHPSESSID = await self.drivefire_session()
        
        down_id = urlparse(url).path.split('/')[2]
        headers = {
            'X-Requested-With':'XMLHttpRequest',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': f'PHPSESSID={PHPSESSID}',
        }
        
        def post():
            r = requests.post(
                'https://drivefire.co/ajax.php?ajax=download',
                data=f'id={down_id}', headers=headers)
            try: return r.json()
            except: return r.text

        r = post()

        attempts=0
        while attempts<3:
            if isinstance(r, dict): break
            r = post()
            attempts+=1


        if isinstance(r, dict):
            direct_dwnld_url = r['file']

            if r['code']=='200':
                self.log(f'Got direct download link: {direct_dwnld_url}')
                return direct_dwnld_url
            
            self.log(r)
        else:
            if retries==0:
                if isfile('trash.bin'): remove('trash.bin')
                await self.drivefire(url, retries=1)
            else:
                self.log('Failed to get direct download link!')


    async def download(self, dwnld_url, destination):
        direct_dwnld_url = await self.drivefire(dwnld_url)
        if direct_dwnld_url:
            self.log(direct_dwnld_url)

            # %cd "$destination"
            user_agent='User-Agent: Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11'
            cmd = f'wget -nv --show-progress --no-check-certificate --content-disposition --header="{user_agent}" "{direct_dwnld_url}"'
            runSh(cmd, output=True)



if __name__ == '__main__':
    async def main():
        # d = Drivefire('angelcutetz@gmail.com', '@AngelCuteTz')
        # await d.drivefire('https://drivefire.co/file/897757269')

        Destination = "/content/drive/Shareddrives/BMS Temp/mkvking/"
        dwnld_url='https://drivefire.co/file/897757269'

        d = Drivefire()
        await d.download(dwnld_url, Destination)
        # await d.drivefire(dwnld_url)
    
    asyncio.run(main())
