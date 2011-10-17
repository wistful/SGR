#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import urllib2

from urllib import urlencode as url_encode
from urllib import quote as url_quote

import re
import json

AUTH_URL = 'https://www.google.com/accounts/ClientLogin'
SUBSCRIPTIONS_LIST_URL = 'http://www.google.com/reader/api/0/subscription/list'
SUBSCRIPTION_URL = 'http://www.google.com/reader/api/0/stream/contents/feed/'


class GReader(object):

    def __init__(self, email=None, pwd=None):
        """
        self.auth(email, pws) if emal and pwd
        """
        self.__clear()
        self.__auth = bool(email and pwd and self.auth(email, pwd))

    def __clear(self):
        """ clear value """
        self.__auth = False
        self.header = {}
        self.subscriptions = []

    def auth(self, email, pwd):
        """
        authorizate to Google Reader service
        """
        self.__clear()
        req_data = url_encode({'Email': email, 'Passwd': pwd, 'service': 'reader', 'accountType': 'GOOGLE'})
        req = urllib2.Request(AUTH_URL, data=req_data)
        try:
            resp = urllib2.urlopen(req).read()
            token = re.search('Auth=(\S*)', resp).group(1)
            self.header = {'Authorization': 'GoogleLogin auth={token}'.format(token=token)}
        except (urllib2.HTTPError, urllib2.URLError) as ex:
            error = "Login Failed:\nerror code: {error_code}\nmsg: {error_msg}\n".format(error_code=ex.code, error_msg=ex.msg)
            logging.log(logging.ERROR, error)
        except AttributeError:
            error = "Token Not Found\response:\n{response}".format(response=resp)
            logging.log(logging.ERROR, error)

        self.__auth = True

    def is_auth(self):
        """
        return True if authorizate, else False
        """
        return self.__auth

    def get_subscriptions(self):
        """
        return subscriptions
        """
        if not self.subscriptions:
            req_data = url_encode({'output': 'json'})
            url = "{subscriptions_list_url}?{req_data}".format(subscriptions_list_url=SUBSCRIPTIONS_LIST_URL, req_data=req_data)
            req = urllib2.Request(url, headers=self.header)
            try:
                resp = urllib2.urlopen(req).read()
                self.subscriptions = json.loads(resp)['subscriptions']
            except (urllib2.HTTPError, urllib2.URLError) as ex:
                error = "Failed getting subscriptions:\nerror code: {error_code}\nmsg: {error_msg}\n".format(error_code=ex.code, error_msg=ex.msg)
                logging.log(logging.ERROR, error)
            except KeyError:
                error = "Subscriptions not found in the response\nResponse:\n{response}".format(response=resp)
                logging.log(logging.ERROR, error)
        return self.subscriptions

    def posts(self, subscription_url, count=20):
        """
        return posts of subscriptions
        """
        req_param = {'r': 'n', 'n': count, 'client': 'scroll'}
        continuation = None
        while 1:
            if continuation:
                req_param['c'] = continuation
            req_data = url_encode(req_param)
            url = "{subscription_url}{subscription}?{req_data}".format(subscription_url=SUBSCRIPTION_URL,
                                                                       subscription=url_quote(subscription_url, ''),
                                                                       req_data=req_data)
            req = urllib2.Request(url, headers=self.header)
            resp = urllib2.urlopen(req).read()
            feed_posts = json.loads(resp)

            for item in feed_posts['items']:
                yield item

            continuation = feed_posts.get('continuation', None)
            if not continuation:
                break

if __name__ == '__main__':
    g = GReader('email', 'password')
    posts = []
    subscription_url = g.get_subscriptions()[3]['id'][5:]
    print("feed: {url}".format(url=subscription_url))
    for post in g.posts(subscription_url):
        date = {'updated': post['updated'], 'published': post['published']}
        content = post['summary']['content']
        url = post['alternate'][0]['href']
        title = post['title']
        posts.append({'date': date, 'content': content, 'url': url, 'title': title})
    print(len(posts))
    for item in posts:
        print('{title}, {url}'.format(title=item['title'].encode('utf8'), url=item['url']))
