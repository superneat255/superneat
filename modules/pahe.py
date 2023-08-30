import re
import json
import asyncio
import requests
import helpers as h
from shlex import split
from subprocess import run
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, quote

try:
    from playwright.async_api import async_playwright
except:
    run(split("sudo pip install playwright"))
    run(split("sudo playwright install"))
    run(split("sudo playwright install-deps"))
    from playwright.async_api import async_playwright


try:
    import js2py
except:
    run(split("sudo pip install js2py"))
    import js2py



class CustomException(Exception):
    def __init__(self, message=''):
        self.message = message
        


class Pahe(object):
    """Made with love by Immanuel Pishon Mwananjela (Superneat)"""
    """superneat2013@gmail.com"""
    

    def __init__(self, debug=True):
        super(Pahe, self).__init__()
        self.debug    = debug
        self.BASE_URL = "https://pahe.li"

        u = self.get_proxy(self.BASE_URL)
        self.sucuri_bypass(u)


    def log(self, s):
        print()
        print( json.dumps(s, indent=4) if isinstance(s, dict) else s )
        print('--------------------------------------')


    def _input(self, instance='int'):
        choice=False
        while not choice:
            try:
                print()
                if instance=='int': choice = int(input('Ingiza namba ya chaguo lako (int): '))
                if instance=='str': choice = input('Ingiza namba ya chaguo lako (str): ')
                print()
            except:
                print('Umekosea hakikisha unaingiza namba kama namba pekee.')
        return choice


    @property
    def headers(self):
        return {'user-agent': "Mozilla/5.0 Chrome/96.0.4664.45 Safari/537.36"}


    @property
    def patterns(self):
        return {
        'MOVIE_PATTERN': r'([\w\s\'\’\:]+\([0-9]{4}\))([\w\&\s\,]+)',
        'COMPLETE_SERIES_PATTERN': r'([\w\s\'\’\:]+Season[0-9\-\s]+)Complete([\w\&\s\,\-]+)',
        'CONTINUING_SERIES_PATTERN': r'([\w\s\'\’\:]+Season[0-9\-\s]+)([\w\&\s\,\-]+\[([\w\d\s]+)\])',
        }


    def get_proxy(self, url):
        u = quote(url)
        return f'https://proxy.downloadapi.workers.dev/api/download?url={u}'
    

    def sucuri_bypass(self, url):
        res = requests.get(url, headers=self.headers)
        scr = re.findall(r'<script>([\s\S]*?)<\/script>', res.text, re.MULTILINE)[0]
        a=(scr.split("(r)")[0][:-1]+"r=r.replace('document.cookie','var cookie');")

        b = (js2py.eval_js(a))

        sucuri_cloudproxy_cookie = js2py.eval_js(b.replace("location.","").replace("reload();",""))
        cookies={sucuri_cloudproxy_cookie.split("=")[0]:sucuri_cloudproxy_cookie.split("=")[1].replace(";path","")}

        self.log(f'Got securi cookie: {cookies}')
        self.s = requests.session()
        self.s.cookies.update(cookies)
        self.s.headers.update(self.headers)


    def metadata(self, title):
        for k,v in self.patterns.items():
            pattern = re.compile(v, flags=re.IGNORECASE)

            match = pattern.search(title)
            if match:
                t,qf = match.groups()
                q = re.sub(r'[0-9]{3,4}p|[\&\,]+', '', qf, flags=re.IGNORECASE).strip()
                f = qf.replace(q, '').strip()
                return {
                    'title': t.strip(),
                    'quality': q,
                    'formats': re.findall('[0-9]{3,4}p', f, flags=re.IGNORECASE),
                    'type': 'movie' if 'MOVIE' in k else 'series',
                }


    async def get(self, url):
        try:
            u = self.get_proxy(url)
            r = self.s.get(u)
            
            retries=0
            while retries<10:
                if 'You are being redirected...' not in r.text: break
                
                await asyncio.sleep(1)
                # self.sucuri_bypass(u)
                r = self.s.get(u)

                retries+=1
            
            if 'You are being redirected...' in r.text:
                raise CustomException('Failed to get contents!')
            
            return r
        
        except CustomException as e: self.log(str(e))


    async def search(self, keywords):
        u = f'{self.BASE_URL}/?s={quote_plus(keywords)}'
        r = await self.get(u)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        contents = soup.find('div', {"class":"timeline-contents"}).find_all('li')

        items=[]
        count=0
        for content in contents:
            a = content.find('h2', {"class":"post-box-title"}).find('a')
            u = a.get('href')
            m = self.metadata(a.text)

            items.append({'title':m['title'], 'url':u, 'quality':m['quality']})

            count += 1
            print(f'{count}.', m['title'], '|', m['quality'], '|', ', '.join(m['formats']))

        # print(json.dumps(items))
        choice=self._input()
        choosen_item_ = items[choice-1]
        choosen_items = await self.download_list(choosen_item_['url'])

        dwnld_urls=[]
        for choosen_item in choosen_items:
            dwnld_url = await self.skip_ads(choosen_item['url'])
            dwnld_url = await self.bypass_linegee(dwnld_url)
            dwnld_urls.append({'name':choosen_item['name'], 'dwnld_url':dwnld_url})

        self.log(dwnld_urls)
        return dwnld_urls


    def get_formats(self, text, formats):
        _format = ''
        for i in text:
            pattern = re.compile('[0-9]{3,4}p', flags=re.IGNORECASE)
            match = pattern.search(i)
            if match: 
                _format = match.group()
            else:
                if '\u00a0' not in i: formats.append(f'{i} {_format}')
        return formats


    async def download_list(self, url):
        r = await self.get(url)

        # print(r.text.encode('utf-8'))

        soup = BeautifulSoup(r.text, 'html.parser')
        download_divs = soup.find_all("div", {'class':'download'})

        count=0
        items=[]
        formats=[]
        for download_div in download_divs:
            text = download_div.text.strip().split("\n")
            
            """
            Button hazina kitu kinachoonyesha ni btn ya format ipi 
            inaonyesha tu source yake kama ni GD, MG n.k 
            Maneno yanayoonyesha formats yamewekwa tu juu halafu chini 
            ndio btn zinafuata (hayapo kwenye tag yoyote maalum)
            Kwahiyo inabidi ku extract formats kutoka kwenye text,
            halafu kulinganisha
            """
            formats.extend(self.get_formats(text, formats))
            
            for a in download_div.find_all("a", {'class':'shortc-button'}):
                url = a.get('href')
                name = formats[count]

                items.append({'name':name, 'url':url})

                print(f'{count+1}.', name)
                count += 1

        choices=self._input(instance='str')
        
        choosen_items=[]
        for choice in choices.split(','):
            choosen_items.append(items[int(choice)-1])
        
        # self.log(choosen_items)
        return choosen_items


    async def skip_ads(self, url):
        async with async_playwright() as p:
            self.log('Opening browser...')
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context()

            page = await context.new_page()
            await page.goto(url)
            
            retries=0
            self.log('Bypassing lite-human-verif-button...')
            while retries<3:
                try: 
                    await page.locator('#lite-human-verif-button').click()
                    break
                except: retries+=1
            self.log('lite-human-verif-button bypassed')
            
            retries=0
            self.log('Bypassing lite-start-sora-button...')
            while retries<3:
                try: 
                    await page.locator('#lite-start-sora-button').click()
                    break
                except: retries+=1
            self.log('lite-start-sora-button bypassed')

            retries=0
            self.log('Bypassing lite-end-sora-button...')
            while retries<3:
                try: 
                    await page.locator('#lite-end-sora-button').click()
                    break
                except: retries+=1
            self.log('lite-end-sora-button bypassed')

            
            self.log('Waiting third party source url...')
            while len(context.pages)<2: await asyncio.sleep(1)

            new_page = context.pages[1]
            dwnld_url = new_page.url
            self.log(f'Got download url: {dwnld_url}')
                
            await browser.close()

        # self.log(dwnld_url)
        return dwnld_url


    async def bypass_linegee(self, linegee_url):
        r = await self.get(linegee_url)
        pattern = re.compile(r"(?<=atob\(')(\w+\=)(?=\'\))", flags=re.IGNORECASE)
        match = pattern.search(r.text)
        if match: return h.b64_decode(match.group())




if __name__ == '__main__':
    async def main():
        p = Pahe()
        await p.search("king's man")
        # await p.download_list("https://pahe.li/the-kings-man-2021-uhd-bluray-720p-1080p-2160p/")
        # await p.bypass_linegee('https://linegee.net/jD7rl')
    
    asyncio.run(main())
