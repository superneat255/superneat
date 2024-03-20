import re
from json import dumps
from bs4 import BeautifulSoup
from urllib.parse import quote
from requests import post, get
from urllib.parse import urlparse



class Waploaded(object):

    body     = None
    endpoint = None
    results  = None
    url      = None
    baseUrl  = 'https://waploaded.com'


    def __init__(self):
        super(Waploaded, self).__init__()


    @property
    def headers(self):
        return {
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
        }
    

    def req(self):
        u = f"{self.baseUrl}{self.endpoint}" if self.url==None else self.url

        if self.body==None:
            return get(u, headers=self.headers).text
        else:
            return post(u, json=self.body, headers=self.headers).text


    def searchItems(self, soup):
        for file_card in soup.find_all("div", {"class": "file_card"}):
            img        = file_card.find("img", {"loading": "lazy"}).get("src")
            file_title = file_card.find("h1", {"class": "file_title"})

            href  = file_title.find("a").get('href')
            title = file_title.get_text().strip()

            regex = re.compile("s[0-9]{1,3}e[0-9]{1,3}", flags=re.IGNORECASE|re.MULTILINE)
            matches = regex.findall(title)

            type_ = 'episode' if matches else 'series'

            self.results.append({
                "title": title,
                "type": type_,
                "url": href,
                "cover": img,
            })


    #_type:series,movie
    def search(self, query, _type='series'):
        self.results = []

        self.endpoint = f"/search/{quote(query)}/page/1?type={_type}"
        html_content  = self.req()

        soup = BeautifulSoup(html_content, 'html.parser')
        self.searchItems(soup)

        pagination_list = soup.find("ul", {"class": "pagination-list"})

        for li in pagination_list.find_all("li"):
            self.endpoint = li.find('a').get("href")
            html_content  = self.req()

            soup = BeautifulSoup(html_content, 'html.parser')
            self.searchItems(soup)


    def episode(self, url):
        urlparse_    = urlparse(url)
        self.baseUrl = f"{urlparse_.scheme}://{urlparse_.netloc}"
        
        self.url     = url
        html_content = self.req()

        soup = BeautifulSoup(html_content, 'html.parser')
        ad_slot = soup.find("div", {"class": "ad-slot"})

        for a in ad_slot.find_all("a"):
            self.download( self.baseUrl+a.get("href") )
            break


    def download(self, url):
        urlparse_    = urlparse(url)
        self.baseUrl = f"{urlparse_.scheme}://{urlparse_.netloc}"
        
        self.url     = url
        html_content = self.req()

        soup    = BeautifulSoup(html_content, 'html.parser')
        a       = soup.find("div", {"class": "ad-slot"}).find_all("a")
        bezende = soup.find("div", {"class": "bezende"})

        self.results = []
        i = 0
        for script in bezende.find_all("script"):
            pattern = r"location.href\s*=\s*'([^']+)'"
            matches = re.findall(pattern, script.get_text())

            self.results.append({
                "text": a[i].get_text().strip(),
                "url": matches[0].strip() if matches else ""
            })

            i+=1


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

        


if __name__ == '__main__':
    from subprocess import run
    from shlex import split

    w = Waploaded()
    w.search("ruthless")
    items = w.results

    i=0
    for item in items:
        print(f"{i+1}. [{item['type']}] {item['title']}")
        i+=1

    choices=w._input('str')

    for choice in choices.split(","):
        choice = int(choice.strip())
        choosen_item_ = items[choice-1]

        w.episode(choosen_item_['url'])
        downloads = w.results

        for download in downloads:
            shellCmd = f"python -m wget {download['url']}"
            run(split(shellCmd))

        # print(dumps(w.results, indent=4))
