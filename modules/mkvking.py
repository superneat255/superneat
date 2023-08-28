import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import quote, quote_plus, urlencode
from playwright.async_api import async_playwright


# url = 'https://84.46.254.230/'
# r = requests.get(url=url, data=data)
# soup = BeautifulSoup(r.text, 'html.parser')
# print(soup)

keywords  = "king's man"
BASE_URL = "https://84.46.254.230"


async def search():
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

    choice=False
    while not choice:
        try:
            print()
            choice = int(input('Ingiza namba ya chaguo lako: '))
        except:
            print()
            print('Umekosea hakikisha unaingiza namba kama namba pekee.')

    choosen_item = items[choice-1]

    # print()
    # print(choosen_item)
    # print()
    await download_list(choosen_item['url'])


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

    choice=False
    while not choice:
        try:
            print()
            choice = int(input('Ingiza namba ya chaguo lako: '))
        except:
            print()
            print('Umekosea hakikisha unaingiza namba kama namba pekee.')

    choosen_item = items[choice-1]
    await skip_ads(choosen_item['url'])


async def skip_ads(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto(url)

        
        retries=0
        while retries<3:
            try: 
                await page.locator('#lite-human-verif-button').click()
                break
            except: retries+=1
        
        retries=0
        while retries<3:
            try: 
                await page.locator('#lite-start-sora-button').click()
                break
            except: retries+=1

        retries=0
        while retries<3:
            try: 
                await page.locator('#lite-end-sora-button').click()
                break
            except: retries+=1

        
        while len(context.pages)<2: await asyncio.sleep(1)

        new_page = context.pages[1]
        new_tab_url = new_page.url
        print(new_tab_url)

        if 'drivefire' in new_tab_url:
            await drivefire(new_tab_url)
        else:
            await asyncio.sleep(20)
            await browser.close()


async def drivefire_login():
    code=''
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto('https://drivefire.co/login')

        await page.locator('#identifierId').type('angelcutetz@gmail.com')
        await asyncio.sleep(2)
        await page.locator('#identifierNext > div > button > span').click()
        await asyncio.sleep(5)
        await page.locator("[name='Passwd']").type('@AngelCuteTz')
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
        PHPSESSID=''
        for cookie in cookies:
            if cookie['name']=='PHPSESSID':
                PHPSESSID=cookie['value']
        
        print('PHPSESSID', PHPSESSID)

        await browser.close()
            



async def drivefire(url):
    down_id = urlparse(url).path.split('/')[2]
    headers = {
        'X-Requested-With':'XMLHttpRequest',
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': 'PHPSESSID=570b6efe8c3a3685ce92cd508c253b38',
        # 'Cookie': 'PHPSESSID=fd1f2d80ec2f1ffb305e5db59fc2fe8d',
    }
    
    def post():
        r = requests.post(
            'https://drivefire.co/ajax.php?ajax=download',
            data=f'id={down_id}', headers=headers)
        try: return r.json()
        except: return r.text

    r = post()
    print(r)



asyncio.run(drivefire_login())
# asyncio.run(search())
