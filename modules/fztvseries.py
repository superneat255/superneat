import re
import json
import asyncio
import requests
from os import remove
from helpers import runSh
from os.path import isfile
from os.path import basename
from bs4 import BeautifulSoup #pip install beautifulsoup4
from urllib.parse import urlparse, unquote, quote
from concurrent.futures import ThreadPoolExecutor, as_completed


class Fztvseries(object):
    """Made with love by Immanuel Pishon Mwananjela (Superneat)"""
    """superneat2013@gmail.com"""

    def __init__(self, workers=2, debug=True):
        super(Fztvseries, self).__init__()
        self.debug    = debug
        self.base_url = "https://fztvseries.live"
        self.results  = []

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


    def rename_series(self, title):
        title = title.replace('_-_', '.').replace('_','.')
        title = title.replace(f".{title.split('.')[-2]}",'')
        return title


    async def search(self, keywords):
        url = f"{self.base_url}/search.php?search={keywords}&beginsearch=Search&vsearch=&by=series"
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
        }
        r = requests.get(url, headers=headers)

        soup = BeautifulSoup(r.text, 'html.parser')
        mainboxes = soup.find_all("div", {"class": "mainbox3", "style": "text-align:left;border-bottom:1px solid grey;"})
        
        self.results = []
        for mainbox in mainboxes:
            table = mainbox.find_all('table')

            if not table:
                self.log(mainbox.text)
                # No Results. Check the spelling or try broadening your search. Or you can also search by specific themes
                return
            else:
                td      = mainbox.find_all('td')
                href    = quote(td[0].find('a').get('href'))
                img_src = f"{self.base_url}/{td[0].find('img').get('src')}"

                t = [small.get_text() for small in td[1].find_all('small')]
                title   = f'{t[0]} {t[1]}'.strip()

                data            = {}
                data['title']   = title
                data['url']     = f"{self.base_url}/{href}"
                data['quality'] = ''
                data['cover']   = img_src
                data['imdb_id'] = ''
                self.results.append(data)
        return self.results

    
    async def choose_series(self):
        count = 0
        for data in self.results:
            count += 1
            print(f'{count}.', data['title'])

        choice=self._input()
        choosen_series = self.results[choice-1]
        return choosen_series


    async def get_available_seasons(self, choosen_series):
        url  = choosen_series['url']
        r    = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        containsSeason = soup.find("div", {"itemprop": "containsSeason"})
        seasons        = containsSeason.find_all("div", {"class": "mainbox2"})

        available_seasons = []
        for season in seasons:
            data          = {}
            data['title'] = season.find('a').get_text()
            data['url']   = self.base_url+"/"+season.find('a').get('href')
            available_seasons.append(data)
        return available_seasons
    

    async def choose_season(self, choosen_series):
        available_seasons = await self.get_available_seasons(choosen_series)

        count=0
        for season in available_seasons:
            count += 1
            print(f'{count}.', season['title'])
        choices=self._input(instance='str')
        
        choosen_seasons=[]
        for choice in choices.split(','):
            choosen_seasons.append(available_seasons[int(choice)-1])
        
        # self.log( json.dumps(choosen_seasons, indent=4) )
        return choosen_seasons


    async def get_season_dld_urls(self, choosen_season):
        season_download_urls = []
        episodes = await self.get_episodes(choosen_season['url'])
        for episode in episodes:
            for option in episode.get('download_options', []):
                if 'mp4' in option['quality'].lower():
                    urls = await self.get_episode_dld_urls(option['url'])
                    
                    season_download_urls.append({
                        "filename": self.rename_series(unquote(basename(urlparse(urls[0]).path))),
                        "urls": urls
                    })
        # print(json.dumps(season_download_urls, indent=4))
        return season_download_urls


    async def get_episode_dld_urls(self, url):
        r = requests.get(url)
        PHPSESSID = r.cookies['PHPSESSID']

        soup = BeautifulSoup(r.text, 'html.parser')
        href = soup.find("a", {"id": "dlink2"}).get('href')
        download_page = f"{self.base_url}/{href}"

        r    = requests.get(url=download_page, headers={'Cookie': f"PHPSESSID={PHPSESSID}"})
        soup = BeautifulSoup(r.text, 'html.parser')
        filelinks = soup.find_all("input", {"name": "filelink"})

        download_urls = []
        for filelink in filelinks:
            download_urls.append(filelink.get('value'))
        return download_urls
    

    async def get_episodes(self, url):
        r        = requests.get(url)
        soup     = BeautifulSoup(r.text, 'html.parser')
        episodes = soup.find_all("div", {"class": "mainbox"})

        available_episodes = []
        for episode in episodes:
            td       = episode.find_all('td')
            thumb    = f"{self.base_url}/{td[0].find('img').get('src')}"
            small    = td[1].find_all('small')
            position = re.findall(r"S[0-9]{2,3}E[0-9]{2,3}", small[0].get_text(), flags=re.IGNORECASE)[0]

            options = []
            for a in td[1].find_all('a'):
                options.append({
                    "url": f"{self.base_url}/{a.get('href')}",
                    "quality": a.get_text()
                })

            data             = {}
            data['title']    = small[0].get_text().split('-')[-1]
            data['position'] = position
            data['download_options'] = options
            available_episodes.append(data)
        return available_episodes


    def download_here(self, season_download):
        filename = season_download['filename']

        for url in season_download['urls']:
            if isfile(filename): return {'status': 'exist', 'filename': filename}

            user_agent = 'User-Agent: Mozilla/5.0 Chrome/96.0.4664.45 Safari/537.36'
            cmd = (  'wget -nv --show-progress --no-check-certificate '
                    f'--header="{user_agent}" -O "{filename}" "{url}"')
            runSh(cmd, output=True, shell=True)

            if isfile(filename):
                return {'status': 'downloaded', 'filename': filename}
                #Use return to prevent re downloading same file
            else:
                remove(filename)

        return {'status': 'failed', 'filename': filename}

    
    def download(self, season_downloads):
        response = []
        futures  = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            for season_download in season_downloads:
                futures.append(pool.submit(self.download_here, season_download))

            for future in as_completed(futures):
                result = future.result()
                response.append(result)
                self.log(f'[{result["status"].upper()}] {result["filename"]}')
        return response
        

if __name__ == '__main__':
    async def main():
        f = Fztvseries()
        await f.search('power')
        choosen_series = await f.choose_series()
        choosen_seasons = await f.choose_season(choosen_series)
        
        for choosen_season in choosen_seasons:
            season_dld_urls = await f.get_season_dld_urls(choosen_season)
            print(season_dld_urls)
            break
    
    asyncio.run(main())
