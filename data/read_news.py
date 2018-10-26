#!/user/bin/python

import json
import sys
import datetime
import urllib.request
from slugify import slugify
import os
import re
import shutil

img_pat = re.compile('<img [^>]*src="([^"]+)')
link_pat = re.compile('href="([^"]+)')

filename = sys.argv[1]
usersfile = sys.argv[2]
outfile = sys.argv[3]


news_img_folder = 'news/'

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
links = []
images = []
image_folders = set()
image_dict = {}
slug_cnt = {}

oldest = datetime_object = datetime.datetime.strptime('2008-01-01', '%Y-%m-%d')

skip_citys = ['tuebingen']

for article in data["news-list"]:
    article = article['news-article']
    dt_obj = datetime.datetime.strptime(article['datetime'], "%Y-%m-%d %H:%M:%S")
    if dt_obj < oldest:
        continue

    dt = dt_obj.isoformat()
    slug_date = dt_obj.strftime("%Y-%m-%d")
    host = article['wb-host'].lower()
    host = umlaute(host)
    if host in skip_citys:
        print(host)
        continue

    user_id = article['Autor']
    user = users[user_id]['name']

    img = article['teaserimage']['src']
    slug = slugify(umlaute(article['article-title'].rstrip().lower()))
    slug = slug_date + '-' + slug

    if slug in slug_cnt:
        slug_cnt[slug] = slug_cnt[slug] + 1
        print("duplicate slug", slug, slug_cnt[slug])
        slug = slug + '-nr' + str(slug_cnt[slug])
        print("add \"nr\" to slug ->", slug)
    else:
        slug_cnt[slug] = 1

    img_ext = os.path.splitext(img)[1].lower()
    if img_ext is 'jpeg':
        img_ext = 'jpg'

    img = re.sub(r'styles/.*/public/', '', img)

    name = slug + img_ext



    if "neues-default" in img:
        name = 'neues-default'

    teaser_image = {
        'url': img,
        'name': name
    }

    if img in image_dict:
        teaser_image['name'] = image_dict[img]['name']
        #print('Image', img, 'already exists.', 'Take name from existing image:', teaser_image['name'])
    else:
        image_dict[img] = teaser_image
        images.append(teaser_image)

    #print(teaser_image)

    text = article['article-text'].rstrip()

    images_html = img_pat.findall(text)
    links_html = link_pat.findall(text)

    i = 1
    for image in images_html:
        img_ext = os.path.splitext(image)[1].lower()
        img_ext = img_ext.split("?")[0]
        if img_ext is 'jpeg':
            img_ext = 'jpg'

        img_dir = os.path.dirname(image)
        image_folders.add(img_dir)
        name = slug + '-' + str(i) + img_ext
        original_path = image
        image = re.sub(r'styles/.*/public/', '', image)

        if not image.startswith("http"):
            continue

        html_image = {
            'url': image,
            'name': name,
        }

        if image in image_dict:
            html_image['name'] = image_dict[image]['name']
            #print('Image', image, 'already exists.', 'Take name from existing image:', html_image['name'])
        else:
            image_dict[image] = html_image
            i = i+1
            images.append(html_image)

        print("Replace", original_path, "with", "/media/" + news_img_folder+html_image['name'])
        text = text.replace(original_path, "/media/" + news_img_folder+html_image['name'])
        #print(html_image)

    for i, link in enumerate(links_html):
        if link.startswith('http://weitblicker.org'):
            links.append({
                'link': link,
                'article': slug
            })
            #print(slug, " -> ", link)

    elem = {
        'title_de': article['article-title'].rstrip(),
        'text_de': text,
        'image': news_img_folder+teaser_image['name'],
        'img_alt_de': article['teaserimage']['alt'],
        'added': dt,
        'updated': dt,
        'published': dt,
        'range': 'global',
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

for folder in image_folders:
    print(folder)

with open(outfile, 'w') as outfile:
    json.dump(news_list, outfile)


folder = 'images'

for i, image in enumerate(images):
    url = image['url']
    name = image['name']

    filename =folder + '/' + name.strip()

    if os.path.isfile(filename):
        print(filename, 'already exists. skip.')
        continue

    print('Download image ', i, 'from', len(images), ':', url, 'to images/'+name)
    with urllib.request.urlopen(url) as response, open(filename, 'wb') as img_file:
        shutil.copyfileobj(response, img_file)

    #### todo download images
    #styles/presselogo_custom_user_normal_1x/public

def download(url, dname):
    urllib.request.urlretrieve(url, dname)

#for dl in downloads:
#    download(dl['url'], "images/" + dl['name'])
