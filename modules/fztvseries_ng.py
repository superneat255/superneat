import re
import json
import time
import asyncio
from helpers import runSh
from os.path import isfile
import requests #pip install requests
import feedparser #pip install feedparser
from bs4 import BeautifulSoup #pip install beautifulsoup4
from urllib.parse import urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed


class FztvseriesNg():
    """Made with love by Immanuel Pishon Mwananjela (Superneat)"""
    """superneat2013@gmail.com"""

    watermark = ''


    def __init__(self, workers=2, debug=True):
        self.workers  = workers
        self.debug    = debug
        self.base_url = "https://fztvseries.ng/"
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


    async def search(self, keywords):
        d = feedparser.parse(f'https://fztvseries.ng/search/{quote_plus(keywords)}/feed/rss2/')
        self.entries = d.get('entries')
        
        self.results = []
        for entry in self.entries:
            if 'media_content' not in entry: continue

            data            = {}
            data['title']   = entry.get('title')
            data['url']     = entry.get('link')
            data['quality'] = ''
            data['cover']   = entry.get('media_content')[0]['url']
            data['imdb_id'] = ''
            data['entry']   = entry
            self.results.append(data)
        return self.results

    
    async def choose_series(self):
        count = 0
        for data in self.results:
            count += 1
            print(f'{count}.', data['title'])

        choice=self._input()
        self.choosen_series = self.results[choice-1]


    async def get_episodes(self):
        rawdata = self.choosen_series.get('entry')['content'][0]['value']

        soup     = BeautifulSoup(rawdata, 'html.parser')
        episodes = soup.find_all("a", {"class": "shortc-button"})

        series_title = self.choosen_series.get('title')
        season_no    = re.findall(r"Se[0-9]{2,3}", series_title, flags=re.IGNORECASE)
        season_no    = re.sub('[^0-9]', '', season_no[0]).zfill(2) if season_no else '01'

        filename = series_title.split('–')[0]
        filename = re.sub(r'[^a-z0-9\s]', '', filename, flags=re.IGNORECASE)
        filename = re.sub(r'Complete|s[0-9]{1,2}', '', filename, flags=re.IGNORECASE).strip()

        available_episodes = []
        for episode in episodes:
            title    = episode.get_text().strip()
            position = f"S{season_no}E{re.sub('[^0-9]', '', title)}"

            data                 = {}
            data['title']        = title
            data['position']     = position
            data['filename']     = f'{filename}.{position}'
            data['dld_page_url'] = episode.get('href')
            available_episodes.append(data)
        return available_episodes


    def get_episode_dld_url(self, url):
        parsed_url = urlparse(url)
        token      = parsed_url.path.split('/')[2]
        dld_url    = None

        h = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        d = f"token={token}&api=1"

        timeout = int(time.time()) + 5
        while int(time.time()) <= timeout:
            try:
                r = requests.post(url, data=d, headers=h)
                if r.status_code == 200:
                    file_url = r.json()['file']
                    dld_url  = file_url if 'http' in file_url else f"{parsed_url.scheme}://{parsed_url.netloc}{file_url}"
                    break
            except: pass
            time.sleep(1)
        return dld_url

    

    def download_here(self, episode):
        try:
            dld_url = self.get_episode_dld_url(episode.get('dld_page_url'))
            # return {'status': 'debug', 'filename': dld_url}

            filename = None

            if dld_url[-4:] in ['.mp4', '.mkv']:
                filename = f"{self.watermark}{episode.get('filename')}{dld_url[-4:]}"
                
            else:
                r = requests.head(dld_url)
                content_disposition = r.headers.get('Content-Disposition')
                if content_disposition:
                    ext = re.findall(r'filename="(.*)"', content_disposition)[0][-4:]
                    filename = f"{self.watermark}{episode.get('filename')}{ext}"

            user_agent = 'User-Agent: Mozilla/5.0 Chrome/96.0.4664.45 Safari/537.36'
            if filename:
                if isfile(filename): return {'status': 'exist', 'filename': filename}

                cmd = (  'wget -nv --show-progress --no-check-certificate '
                        f'--header="{user_agent}" -O "{filename}" "{dld_url}"'
                        )
            else:
                cmd = (  'wget -nv --show-progress --no-check-certificate '
                        f'--header="{user_agent}" "{dld_url}"'
                        )

            runSh(cmd, output=True, shell=True)
            return {'status': 'downloaded', 'filename': filename}
        except Exception as e:
            return {'status': 'failed', 'filename': str(e)}

    
    def download(self, episodes):
        response = []
        futures  = []
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            for episode in episodes:
                futures.append(pool.submit(self.download_here, episode))

            for future in as_completed(futures):
                result = future.result()
                response.append(result)
                self.log(f'[{result["status"].upper()}] {result["filename"]}')
        return response
        

if __name__ == '__main__':
    async def main():
        f = FztvseriesNg()
        f.watermark = '@bmsflix.'
        await f.search('youngins')
        choosen_series = await f.choose_series()
        episodes = await f.get_episodes()
        # f.download_here(episodes[0])
        f.download(episodes)
    
    asyncio.run(main())