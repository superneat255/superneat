"""***************************************************
 * Python 3.10.0 
 * Created by: Immanuel Pishon Mwananjela
 * Email: +255 752 104 228, superneat2013@gmail.com
 *//////////////////////////////////////////////////"""

from requests import get, post


class Telegraph(object):

    base_url = 'https://api.telegra.ph'

    
    def __init__(self, access_token):
        super(Telegraph, self).__init__()
        self.access_token = access_token

    
    def req(self, endpoint, data=None):
        headers   = {
            'Content-Type':'application/json',
            'Accept':'application/json',
        }

        url = f'{self.base_url}/{endpoint}'
        
        if data!=None:
            data['access_token'] = self.access_token
            r = post(url, json=data, headers=headers)
        
        else: r = get(url, headers=headers)
        
        return r.json()


    def createAccount(self, short_name, author_name='', author_url=''):
        return self.req('createAccount', {
                'short_name': short_name,
                'author_name': author_name,
                'author_url': author_url,
            })


    #Pass only the parameters that you want to edit.
    def editAccountInfo(self, short_name='', author_name='', author_url=''):
        return self.req('createAccount', {
                'short_name': short_name,
                'author_name': author_name,
                'author_url': author_url,
            })


    def getAccountInfo(self):
        return self.req('getAccountInfo', {
                'fields': ['short_name','author_name','author_url','auth_url','page_count'],
            })


    def revokeAccessToken(self):
        return self.req('revokeAccessToken', {})


    def createPage(self, title, content, return_content=False):
        return self.req('createPage', {
                'title': title,
                'content': content,
                'return_content': return_content,
            })


    def getPage(self, path, return_content=False):
        return self.req('getPage', {
                'path': path,
                'return_content': return_content,
            })


    def editPage(self, path, title, content, return_content=False):
        return self.req('editPage', {
                'path': path,
                'title': title,
                'content': content,
                'return_content': return_content,
            })
