import re
import json
import asyncio
import requests
from os import remove
from helpers import runSh
from os.path import isfile
from os.path import basename
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import unquote, quote
from concurrent.futures import ThreadPoolExecutor, as_completed




class Fzmovies(object):
    """Made with love by Immanuel Pishon Mwananjela (Superneat)"""
    """superneat2013@gmail.com"""


    def __init__(self, debug=True):
        super(Fzmovies, self).__init__()
        self.debug    = debug
        self.base_url = "https://fzmovies.net"


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
        url = f"{self.base_url}/csearch.php"
        r = requests.post(url, data={
                'searchname' : keywords,
                'Search'     : 'Search',
                'searchby'   : 'Name',
                'category'   : 'All',
                'vsearch'    : '',
            })
        
        soup = BeautifulSoup(r.text, 'html.parser')
        mainboxes = soup.find_all("div", {"class": "mainbox"})

        rows  = []
        count = 0
        for mainbox in mainboxes:
            table = mainbox.find_all('table')

            if not table:
                self.log(mainbox.text)
                # No Results. Check the spelling or try broadening your search. Or you can also search by specific themes
                return
            else:
                td   = mainbox.find_all('td')
                href = quote(td[0].find('a').get('href'))
                img  = f"{self.base_url}{td[0].find('img').get('src')}"

                t = [small.get_text() for small in td[1].find_all('small')]
                title = f'{t[0]} {t[1]}'

                data            = {}
                data['title']   = title
                data['url']     = f"{self.base_url}/{href}"
                data['quality'] = re.sub(r'\(|\)', '', t[2])
                data['cover']   = img

                rows.append(data)

                count += 1
                print(f'{count}.', data['title'], '|', data['quality'])

        choice=self._input()
        choosen_item = rows[choice-1]
        # self.log(choosen_item)

        choosen_items = await self._download1(choosen_item['url'])
        return choosen_items



    async def _download1(self, url):
        r = requests.get(url)
        PHPSESSID = r.cookies['PHPSESSID']
        
        soup = BeautifulSoup(r.text, 'html.parser')
        moviesfiles = soup.find_all("ul", {"class": "moviesfiles"})

        rows  = []
        count = 0
        for moviefile in moviesfiles:
            title = moviefile.find('font').get_text()
            href  = self.base_url+"/"+moviefile.find_all('a')[0].get('href')

            a = (self.base_url+moviefile.find_all('a')[0].get_text()).lower()
            _format = re.findall(r"[0-9]{3,4}p", a, flags=re.IGNORECASE)[0]

            dcounter = moviefile.find('dcounter').get_text()
            size = re.findall(r"(?<=\()(.*)(?=\))", dcounter, flags=re.IGNORECASE)[0]

            download_options = await self._download2(PHPSESSID, href)

            options=[]
            for download_option in download_options:
                options.append({
                    'connections': int(re.sub(r'\D', '', download_option['connections'])),
                    'download_link': download_option['download_link'],
                })

            data                 = {}
            data['title']        = f'{title} {_format} | {size}'
            data['message_text'] = href
            data['download_options'] = options

            rows.append(data)

            count += 1
            print(f'{count}.', data['title'])

        if not rows: return 'Hakuna chaguo la format lililopatikana!'
        choices=self._input(instance='str')
        
        choosen_items=[]
        for choice in choices.split(','):
            choosen_items.append(rows[int(choice)-1])
        
        # self.log( json.dumps(choosen_items, indent=4) )
        return choosen_items


    
    async def _download2(self, PHPSESSID, href):
        download_options = []

        headers = {
            'Cookie': f"PHPSESSID={PHPSESSID}"
        }
        r = requests.get(url=href, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        downloadlink = soup.find("a", {"id": "downloadlink"}).get('href')
        downloadlink = f"{self.base_url}/{downloadlink}"

        r2 = requests.get(url=downloadlink, headers=headers)
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        inputs = soup2.find_all('input', {'name': 'download1'})

        i = 0
        for _input in inputs:
            download_link = (_input.get('value')).replace('?fromwebsite', '').replace(' ', '%20')

            for parent in _input.parents:
                if parent.name == 'li':
                    dcounter = parent.find('dcounter').get_text()
                    download_options.append({'connections':dcounter, 'download_link':download_link})
            i+=1
        return download_options



    def download_here(self, row):
        for item in row['download_options']:
            download_link = item['download_link']

            x = requests.head(download_link, timeout=5)
            if x.status_code<200 or x.status_code>=300: continue

            filename = unquote(basename(urlparse(download_link).path))
            if isfile(filename): return f'[File Exist] {filename}'

            user_agent = 'User-Agent: Mozilla/5.0 Chrome/96.0.4664.45 Safari/537.36'
            cmd = (  'wget -nv --show-progress --no-check-certificate '
                    f'--header="{user_agent}" -O "{filename}" "{download_link}"')
            runSh(cmd, output=True, shell=True)

            if isfile(filename):
                return f'[Downloaded] {filename}'
                #Use return to prevent re downloading same file
            
            else:
                remove(filename)

        return f'[Failed] {filename}'


    
    def download(self, choosen_items):
        futures = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            for row in choosen_items:
                futures.append(pool.submit(self.download_here, row))

            for future in as_completed(futures):
                self.log(future.result())
        


if __name__ == '__main__':
    async def main():
        f = Fzmovies()
        await f.search("meg")
    
    asyncio.run(main())
