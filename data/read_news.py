#!/user/bin/python

import json
import sys
import datetime
import urllib.request
from slugify import slugify
import os

filename = sys.argv[1]
usersfile = sys.argv[2]
outfile = sys.argv[3]



def umlaute(value):
    replacements = [(u'ä', u'ae'), (u'ü', u'ue'), (u'ö', u'oe'), (u'gesamtverein', u'bundesverband')]
    for (s, r) in replacements:
        value = value.replace(s, r)
    return value


with open(filename) as f:
    data = json.load(f)

with open(usersfile) as uf:
    user_data = json.load(uf)

users = {}

for user in user_data['users']:

    user = user['user']
    name = user['name']
    mail = user['E-Mail']
    uid = user['uid']
    users[uid] = {
        'name': name,
        'mail': mail
    }

news_list = []
downloads = []

skip_citys = ['tuebingen']

for article in data["news-list"]:
    article = article['news-article']
    dt = datetime.datetime.strptime(article['datetime'], "%Y-%m-%d %H:%M:%S").isoformat()
    host = article['wb-host'].lower()
    host = umlaute(host)
    if host in skip_citys:
        print(host)
        continue

    user_id = article['Autor']
    user = users[user_id]['name']

    img = article['teaserimage']['src']
    slug = slugify(article['article-title'].rstrip())
    img_ext = os.path.splitext(img)[1].lower()

    download = {
        'url': img,
        'name': slug + img_ext
    }

    downloads.append(download)

    elem = {
        'title_de': article['article-title'].rstrip(),
        'text_de': article['article-text'].rstrip(),
        'image': "posts/"+download['name'],
        'img_alt_de': article['teaserimage']['alt'],
        'added': dt,
        'updated': dt,
        'published': dt,
        'range': 'preview',
        'teaser_de': article['conclusion'],
        'host': host,
        "project": None,
        "author": None,
        "author_str": user
    }

    post = {
        "model": "wbcore.post",
        "pk": None,
        "fields": elem
    }

    news_list.append(post)

news_list.sort(key=lambda x: x['fields']['published'], reverse=False)

with open(outfile, 'w') as outfile:
    json.dump(news_list, outfile)


def download(url, dname):
    urllib.request.urlretrieve(url, dname)

#for dl in downloads:
#    download(dl['url'], "images/" + dl['name'])
