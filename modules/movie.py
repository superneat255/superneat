import re
import asyncio
import requests


class Movie(object):
    """Made with love by Immanuel Pishon Mwananjela (Superneat)"""
    """superneat2013@gmail.com"""
    
    def __init__(self, debug=False):
        super(Movie, self).__init__()
        self.debug = debug

        u = 'https://raw.githubusercontent.com/superneat255/superneat/json/MOVIE_RENAMING_REPLACE_LIST.json'
        self.replace_list = requests.get(u).json()


    def log(self, s):
        if not self.debug: return
        print()
        print( json.dumps(s, indent=4) if isinstance(s, dict) or isinstance(s, list) else s )
        print('--------------------------------------')

    
    async def rename(self, title, initial=''):
        for replace in self.replace_list:
            if replace in title:
                title = re.sub(re.escape(replace), '', title, flags=re.IGNORECASE)

        if 'fzmovies' in title:
            t = title.replace('_high_', '.480p.').replace('_','.').replace('(','').replace(')','')
            title = t.split('.fzmovies')[0]+t[-4:]
            l = re.findall(r'[0-9]{4}', title)
            if len(l) == 2: title = title.replace(f"{l[0]}.{l[1]}", l[0])
            

        #Remove timestamps
        title = re.sub('[0-9]{10}', '', title, flags=re.IGNORECASE)

        #More than one dot to single dot
        # title = re.sub(r'[\.\.]+', '', title, flags=re.IGNORECASE)

        #More than one space to single space
        # title = re.sub(r'[\s]+', '', title, flags=re.IGNORECASE)

        title = title.strip().replace(' ', '.')
        if not title.startswith(initial): title=initial+title
        self.log(title)
        return title



if __name__ == '__main__':
    async def main():        
        m = Movie(debug=True)
        title = 'Indiana.Jones.and.the.Dial.of.Destiny.2023.480p.WEB-DL.x264-Pahe.in'
        await m.rename(title, '@bongohits_group.')
    
    asyncio.run(main())
