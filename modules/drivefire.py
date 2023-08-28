import asyncio
import requests
from os.path import isfile
from urllib.parse import urlparse
from subprocess import run
from shlex import split
from os import remove
from helpers import runSh

try:
    from playwright.async_api import async_playwright
except:
    run(split("sudo pip install playwright"))
    run(split("sudo playwright install"))
    run(split("sudo playwright install-deps"))
    from playwright.async_api import async_playwright


debug=True


def log(t):
    if debug==True: print(t)


async def drivefire_session():
    PHPSESSID=''
    if isfile('trash.bin'):
        with open('trash.bin', 'r') as f: PHPSESSID = f.read()
        log('Drivefire saved session found...')
        return PHPSESSID

    log('Drivefire session not found, regenerating...')

    code=''
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
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
        for cookie in cookies:
            if cookie['name']=='PHPSESSID':
                PHPSESSID=cookie['value']
        
        await browser.close()
    
    if PHPSESSID:
        log(f'Got PHPSESSID: {PHPSESSID}')
        with open('trash.bin', 'w') as f: f.write(PHPSESSID)
        return PHPSESSID
            


async def drivefire(url):
    try:
        PHPSESSID = await drivefire_session()
    except:
        log('Failed to get PHPSESSID, input manually!')
        PHPSESSID = input('Ingiza namba ya chaguo lako: ')

    
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
    if isinstance(r, dict):
        direct_dwnld_url = r['file']
        return direct_dwnld_url
    else:
        if isfile('trash.bin'): remove('trash.bin')
        await drivefire(url)



async def download(dwnld_url, destination):
    direct_dwnld_url = await drivefire(dwnld_url)
    log(direct_dwnld_url)

    runSh(f'cd "{destination}"', output=True)
    cmd = f'wget -nv --show-progress --no-check-certificate --content-disposition --header="User-Agent: Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11" "{direct_dwnld_url}"'
    runSh(cmd, output=True)
