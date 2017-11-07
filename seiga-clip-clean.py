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
import requests
import json
import configparser

from argparse import ArgumentParser
from bs4 import BeautifulSoup

options = None

def parse_command_line(args=None):
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
        help='user email or tel'
    )
    parser.add_argument(
        '-p',
        '--password',
        help='user password'
    )
    parser.add_argument(
        '-c',
        '--config',
        help='user config from file'
    )
    parser.add_argument(
        '-q',
        '--quite',
        action='store_true',
        help='quite log'
    )
    parser.add_argument(
        '--detect-no-disp',
        action='store_true',
        help='detect no disp image'
    )
    if args:
        options = parser.parse_args(args)
    else:
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


def qprint(m):
    if not options.quite:
        print(m)


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
    r = seiga.get_page(clipid, page)
    soup = BeautifulSoup(r.text, "html.parser")
    if soup.find(class_='clip_empty'):
        return None
    delete_lists = soup.find_all(attrs={'src': '/img/common/deleted.png'})
    messages = []
    for d in delete_lists:
        root = get_clip_list_root(d.parent)
        messages.append('{0:2d}:{1}:'.format(page, get_clip_id(root)) + get_clip_title(root).strip())
    if options.detect_no_disp:
        no_disp_lists = soup.find_all(attrs={'src': '/img/common/pic_no_disp.gif'})
        for d in no_disp_lists:
            root = get_clip_list_root(d.parent)
            messages.append('{0:2d}:{1}:'.format(page, get_clip_id(root)) + get_clip_title(root).strip())
    return messages


def listup_deleted_clip_in_clip(seiga, clipid):
    messages = []
    for i in range(1, 26):
        page_messages = listup_deleted_clip_in_page(seiga, clipid, i)
        if page_messages is None:
            break
        messages.extend(page_messages)
    return messages


def listup_deleted_clip(seiga):
    r = seiga.get_myclip()
    soup = BeautifulSoup(r.text, "html.parser")
    illust = soup.find(id='my_menu_illust')
    count = 0
    if illust:
        for li in illust.find_all(class_='clip_item'):
            id = li.a.get('href').split('/')[-1]
            messages = listup_deleted_clip_in_clip(seiga, id)
            n = len(messages)
            if n > 0 or not options.quite:
                print(li.find(class_='clip_item_title').text)
                for m in messages:
                    print(m)
                count += n
                print('total: ' + str(n))
                print('----------')
    return count


def login(seiga):
    return seiga.login(options.user, options.password)


def main():
    #sys.stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout, errors='ignore')
    #sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    #sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    global options
    options, others = parse_command_line()
    if options.config:
        config = configparser.ConfigParser()
        config.read(options.config)
        options.user = config.get('options', 'user')
        options.password = config.get('options', 'password')
    seiga = SeigaClip()
    if not login(seiga):
        if options.user:
            print(type(options.user))
        print('login failed...')
        exit(1)
    if listup_deleted_clip(seiga) > 0:
        exit(1)


if __name__ == '__main__':
    main()
