#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# seiga-clip-clean.py
#
# Copyright (C) 2017, srz_zumix
# This software is released under the MIT License,
# see LICENSE
#

import os
import io
import codecs
import sys
import re
import requests
import json

from argparse import ArgumentParser
from bs4 import BeautifulSoup

options = None

def parse_command_line():
    parser = ArgumentParser()
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=u'%(prog)s version 0.1'
    )
    parser.add_argument(
        '-u',
        '--user',
        required=True,
        help='user email or tel'
    )
    parser.add_argument(
        '-p',
        '--password',
        required=True,
        help='user password'
    )
    options = parser.parse_args()
    return options, parser


class SeigaClip:
    """niconico seiga clip"""
    seiga_url = 'http://seiga.nicovideo.jp/'
    login_url = 'https://secure.nicovideo.jp/secure/login'
    myclip_url = 'http://seiga.nicovideo.jp/my/clip'
    nico_id = ''
    session = requests.Session()


    def get_myclip(self):
        r = self.session.get(self.myclip_url)
        r.raise_for_status()
        return r

    def get_page(self, id, page):
        payload = {'page': page, 'sort': 'clip_number'}
        r = self.session.get(self.myclip_url + '/' + str(id), params=payload)
        r.raise_for_status()
        return r

    def is_login(self, response):
        if response.headers['x-niconico-authflag'] != "0":
            return True
        else:
            return False

    def _login(self, user, password):
        r = self.session.get(self.login_url)
        payload = { u'mail_tel': user, u'password': password, u'next_url': '/' }
        #soup = BeautifulSoup(r.text, "html.parser")
        #auth_id = soup.find(attrs={'name': 'auth_id'})
        #if auth_id:
        #    payload['auth_id'] = auth_id.get('value')
        #else:
        #    payload['auth_id'] = self.session.cookies['nicosid']
        r = self.session.post(self.login_url, data=payload, headers={"Referer":"http://com.nicovideo.jp/search/"})
        r.raise_for_status()
        if not self.is_login(r):
            return False
        self.nico_id = r.headers['x-niconico-id']
        return True

    def login(self, user, password):
        return self._login(user, password)


def format_text(t):
    return t.strip('\xa0')


def current_text(d):
    return d.find_all(text=True, recursive=False)


def get_clip_list_root(d):
    if 'class' in d.attrs:
        if 'illust_box_li' in d.attrs['class']:
            return d.parent
    return get_clip_list_root(d.parent)


def get_clip_id(d):
    inputbox = d.find(attrs={'name': 'image_check'})
    if inputbox:
        return inputbox.attrs['value']
    return None


def get_clip_title(d):
    ttl = d.find(attrs={'class': 'text_ttl'})
    if ttl:
        return ttl.text
    return None


def clean_clip(seiga):
    r = seiga.get_page(1533753, 1)
    soup = BeautifulSoup(r.text, "html.parser")
    delete_lists = soup.find_all(attrs={'src': '/img/common/deleted.png'})
    for d in delete_lists:
        root = get_clip_list_root(d.parent)
        print(get_clip_id(root) + ':' + get_clip_title(root))


def listup_deleted_clip_in_page(seiga, clipid, page):
    count = 0
    r = seiga.get_page(clipid, page)
    soup = BeautifulSoup(r.text, "html.parser")
    if soup.find(class_='clip_empty'):
        return -1
    delete_lists = soup.find_all(attrs={'src': '/img/common/deleted.png'})
    for d in delete_lists:
        root = get_clip_list_root(d.parent)
        print('{0:2d}:{1}:'.format(page, get_clip_id(root)) + get_clip_title(root).strip())
        count += 1
    return count


def listup_deleted_clip_in_clip(seiga, clipid, title):
    count = 0
    if title:
        r = seiga.get_page(clipid, 1)
        soup = BeautifulSoup(r.text, "html.parser")
        title_text = soup.find(class_='title_text')
        if title_text:
            print(title_text.a.text)
    for i in range(1, 26):
        n = listup_deleted_clip_in_page(seiga, clipid, i)
        if n < 0:
            break
        count += n
    print('total: ' + str(count))


def listup_deleted_clip(seiga):
    r = seiga.get_myclip()
    soup = BeautifulSoup(r.text, "html.parser")
    illust = soup.find(id='my_menu_illust')
    if illust:
        for li in illust.find_all(class_='clip_item'):
            print(li.find(class_='clip_item_title').text)
            id = li.a.get('href').split('/')[-1]
            listup_deleted_clip_in_clip(seiga, id, False)
            print('----------')


def login(seiga):
    return seiga.login(options.user, options.password)


def main():
    sys.stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout, errors='ignore')
    #sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    #sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    global options
    options, others = parse_command_line()
    seiga = SeigaClip()
    if not login(seiga):
        print('login failed...')
        exit(1)
    listup_deleted_clip(seiga)


if __name__ == '__main__':
    main()
