import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from subprocess import run
from shlex import split

try:
    from playwright.async_api import async_playwright
except:
    run(split("sudo pip install playwright"))
    run(split("sudo playwright install"))
    run(split("sudo playwright install-deps"))
    from playwright.async_api import async_playwright



BASE_URL = "https://84.46.254.230"
debug = True


def log(t):
    if debug==True: print(t)


def _input():
    choice=False
    while not choice:
        try:
            print()
            choice = int(input('Ingiza namba ya chaguo lako: '))
            print()
        except:
            print('Umekosea hakikisha unaingiza namba kama namba pekee.')
    return choice


async def search(keywords):
    url = f'{BASE_URL}/?s={quote_plus(keywords)}&post_type%5B%5D=post&post_type%5B%5D=tv'

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

    choice=_input()
    choosen_item = items[choice-1]
    choosen_item2 = await download_list(choosen_item['url'])
    dwnld_url = await skip_ads(choosen_item2['url'])
    return dwnld_url



async def download_list(url):
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

    choice=_input()
    choosen_item = items[choice-1]
    return choosen_item



async def skip_ads(url):
    async with async_playwright() as p:
        log('Opening browser...')
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto(url)

        
        retries=0
        log('Bypassing lite-human-verif-button...')
        while retries<3:
            try: 
                await page.locator('#lite-human-verif-button').click()
                break
            except: retries+=1
        log('lite-human-verif-button bypassed')
        
        retries=0
        log('Bypassing lite-start-sora-button...')
        while retries<3:
            try: 
                await page.locator('#lite-start-sora-button').click()
                break
            except: retries+=1
        log('lite-start-sora-button bypassed')

        retries=0
        log('Bypassing lite-end-sora-button...')
        while retries<3:
            try: 
                await page.locator('#lite-end-sora-button').click()
                break
            except: retries+=1
        log('lite-end-sora-button bypassed')

        
        log('Waiting third party source url...')
        while len(context.pages)<2: await asyncio.sleep(1)

        new_page = context.pages[1]
        dwnld_url = new_page.url
        log(f'Got download url: {dwnld_url}')
        
        await browser.close()

    return dwnld_url



if __name__ == '__main__':
    keywords = "king's man" #@param {type:"string"}
    asyncio.run(search(keywords))
