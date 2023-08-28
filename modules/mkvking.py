import json
import asyncio
import requests
from shlex import split
from subprocess import run
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

try:
    from playwright.async_api import async_playwright
except:
    run(split("sudo pip install playwright"))
    run(split("sudo playwright install"))
    run(split("sudo playwright install-deps"))
    from playwright.async_api import async_playwright




class Mkvking(object):
    """Made with love by Immanuel Pishon Mwananjela (Superneat)"""
    """superneat2013@gmail.com"""
    

    def __init__(self, debug=True):
        super(Mkvking, self).__init__()
        self.debug    = debug
        self.BASE_URL = "https://84.46.254.230"


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



    async def search(self, keywords):
        url = f'{self.BASE_URL}/?s={quote_plus(keywords)}&post_type%5B%5D=post&post_type%5B%5D=tv'

        r = requests.get(url=url, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = soup.find_all("article")

        items=[]
        count=0
        for article in articles:
            a = article.find('h2', {"class":"entry-title"}).find('a')
            quality = article.find('div', {"class":"gmr-quality-item"}).text
            url = a.get('href')
            title = a.text

            items.append({'title':title, 'url':url, 'quality':quality})

            count += 1
            print(f'{count}.', title, '|', quality)

        choice=self._input()
        choosen_item_ = items[choice-1]
        choosen_items = await self.download_list(choosen_item_['url'])

        dwnld_urls=[]
        for choosen_item in choosen_items:
            dwnld_url = await self.skip_ads(choosen_item['url'])
            dwnld_urls.append({'name':choosen_item['name'], 'dwnld_url':dwnld_url})

        self.log(dwnld_urls)
        return dwnld_urls


    async def download_list(self, url):
        r = requests.get(url=url, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        ul = soup.find("ul", {'class':'gmr-download-list'})
        options = ul.find_all("li")

        items=[]
        count=0
        for option in options:
            a = option.find('a')
            url = a.get('href')
            name = a.text

            items.append({'name':name, 'url':url})

            count += 1
            print(f'{count}.', name)

        choices=self._input(instance='str')
        
        choosen_items=[]
        for choice in choices.split(','):
            choosen_items.append(items[int(choice)-1])
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

        self.log(dwnld_url)
        return dwnld_url




if __name__ == '__main__':
    async def main():
        d = Mkvking()
        await d.search("king's man")
    
    asyncio.run(main())
