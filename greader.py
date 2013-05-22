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
        Initializes GReader instance
        and authorizate if 'email' and 'pwd' setted
        Args:
            email - email address
            pwd - password
        """
        self._header = {}
        self._subscriptions = []
        self.__auth = bool(email and pwd and self.auth(email, pwd))

    def auth(self, email, pwd):
        """
        authorization to Google Reader service
        Args:
            email - email address
            pwd - password
        """
        req_data = url_encode(
            {'Email': email,
             'Passwd': pwd,
             'service': 'reader',
             'accountType': 'GOOGLE'})
        req = urllib2.Request(AUTH_URL, data=req_data)
        try:
            resp = urllib2.urlopen(req).read()
            token = re.search('Auth=(\S*)', resp).group(1)
            self._header = {
                'Authorization': 'GoogleLogin auth={token}'.format(
                    token=token)}
        except (urllib2.HTTPError, urllib2.URLError) as exc:
            logging.error("Login Failed.", extra={'err_code': exc.code,
                                                  'err_message': exc.msg})
        except AttributeError:
            logging.error("Token Not Found in the response.",
                          extra={'response': resp})
        self.__auth = True

    @property
    def is_auth(self):
        """
        return True if authorizate, else False
        """
        return self.__auth

    @property
    def subscriptions(self):
        """
        return subscriptions
        """
        if not self._subscriptions:
            req_data = url_encode({'output': 'json'})
            url = "{subscriptions_list_url}?{req_data}".format(
                subscriptions_list_url=SUBSCRIPTIONS_LIST_URL,
                req_data=req_data)
            req = urllib2.Request(url, headers=self._header)
            try:
                resp = urllib2.urlopen(req).read()
                self._subscriptions = json.loads(resp)['subscriptions']
            except (urllib2.HTTPError, urllib2.URLError) as exc:
                logging.error("Failed getting subscriptions.",
                              extra={'err_code': exc.code,
                                     'err_message': exc.msg})
            except KeyError:
                logging.error("Subscriptions not found in the response.",
                              extra={'response': resp})
        return self._subscriptions

    def posts(self, subscription_url, count=20):
        """
        return posts of subscriptions
        """
        req_param = {'r': 'n', 'n': count, 'client': 'scroll'}
        continuation = None
        while True:
            if continuation:
                req_param['c'] = continuation
            req_data = url_encode(req_param)
            url = "{subscription_url}{subscription}?{req_data}".format(
                subscription_url=SUBSCRIPTION_URL,
                subscription=url_quote(subscription_url, ''),
                req_data=req_data)
            req = urllib2.Request(url, headers=self._header)
            resp = urllib2.urlopen(req).read()
            feed_posts = json.loads(resp)

            for post in feed_posts['items']:
                yield post

            continuation = feed_posts.get('continuation', None)
            if not continuation:
                break

if __name__ == '__main__':
    g = GReader('email', 'password')
    print("Subscriptions:")
    for subscription in g.subscriptions:
        print(subscription['title'], subscription['id'][5:])
    posts = []
    subscription_url = 'http://planet.python.org/rss20.xml'
    print("\nfeed: {url}\n\n".format(url=subscription_url))
    for i, post in enumerate(g.posts(subscription_url)):
        date = {'updated': post['updated'], 'published': post['published']}
        url = post['alternate'][0]['href']
        title = post['title']
        print('{index}, {title}, {url}'.format(
              index=i, date=date, title=title.encode('utf8'), url=url))
