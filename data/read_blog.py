#!/user/bin/python

import re
import json
import sys
import datetime
import urllib.request
from slugify import slugify
import os
import getpass
import pymysql
from urllib import request, error
import shutil
import paramiko
import pandas as pd
from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder
from os.path import expanduser

filename = sys.argv[1]
pw = getpass.getpass()
user = getpass.getuser()

img_pat = re.compile(r'<img [^>]*src="([^"]+)')
img_org = re.compile(r'(-\d+x\d+)')
link_pat = re.compile(r'href="([^"]+)')
p_tag_pat = re.compile(r'(<p>.+?</p>)|(<img.+?src=".+?".*?>)')


home = expanduser('~')
#mypkey = paramiko.RSAKey.from_private_key_file(home + pkeyfilepath)
# if you want to use ssh password use - ssh_password='your ssh password', bellow

sql_hostname = 'localhost'
sql_username = 'root'
sql_password = pw
sql_main_database = 'weitweg-blog'
sql_port = 3306

ssh_host = 'weitblicker.org'
ssh_user = 'spuetz'
ssh_port = 22
ssh_pw = pw

query = '''select p.ID, p.post_title as title, p.post_excerpt as excerpt, p.post_content as content, p.post_date as 'date', p.post_date_gmt as date_gmt, u.user_login, u.display_name, u.ID as user_id, u.user_email, t.name as country, GROUP_CONCAT(p2.Tag) as tags, p.guid as old_page from wp_posts p 
left join wp_users u on p.post_author=u.ID 
inner join wp_term_relationships r on r.object_id=p.ID
inner join wp_term_taxonomy tax on r.term_taxonomy_id=tax.term_taxonomy_id
inner join wp_terms t on tax.term_id=t.term_id
left join (select p2.ID, t2.name as Tag from wp_posts p2 inner join wp_term_relationships r2 on r2.object_id=p2.ID
inner join wp_term_taxonomy tax2 on r2.term_taxonomy_id=tax2.term_taxonomy_id
inner join wp_terms t2 on tax2.term_id=t2.term_id where tax2.taxonomy = 'post_tag' ) p2 on p2.ID=p.ID
where p.post_type='post' and tax.taxonomy = 'category' and
t.name!='unsere Projekte' and p.post_status = 'publish' group by p.ID'''


with SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_password=ssh_pw,
        remote_bind_address=(sql_hostname, sql_port)) as tunnel:
    conn = pymysql.connect(host='127.0.0.1', user=sql_username, passwd=sql_password,
                           db=sql_main_database, port=tunnel.local_bind_port)
    df = pd.read_sql_query(query, conn)
    conn.close()



#
# [{"model": "wbcore.blogpost", "pk": 1,
#   "fields": {
#       "title": "BeispielTitel",
#       "title_de": "BeispielTitel", "title_en": null, "title_fr": null,
#       "text": "<p>BeispielText</p>", "text_de": "<p>BeispielText</p>", "text_en": "", "text_fr": "",
#       "image": "", "img_alt": "BeispielImgAlt",
#       "img_alt_de": "BeispielImgAlt", "img_alt_en": null,"img_alt_fr": null,
#       "added": "2018-10-22T06:21:25.035Z", "updated": "2018-10-22T06:21:25.035Z",
#       "published": "2018-10-22T06:21:25.035Z", "range": "global", "teaser": "<p>Beispiel Teaser</p>",
#       "teaser_de": "<p>Beispiel Teaser</p>", "teaser_en": "", "teaser_fr": "", "host": "bundesverband",
#       "project": null, "author": null, "author_str": "BeispielAuthor", "gallery": null}}]


def umlaute(value):
    replacements = [(u'ä', u'ae'), (u'ü', u'ue'), (u'ö', u'oe'), (u'gesamtverein', u'bundesverband')]
    for (s, r) in replacements:
        value = value.replace(s, r)
    return value


post_list = []
images = []

for index, article in df.iterrows():

    dt_obj = pd.to_datetime(article['date'], format="%Y-%m-%d %H:%M:%S")
    slug_date = dt_obj.strftime("%Y-%m-%d")
    dt = dt_obj.tz_localize('UTC').strftime("%Y-%m-%d %H:%M:%S.%f")

    host = None
    user = article['user_login']
    text = article['content']
    title = article['title'],
    title = title[0]
    image = None
    images_html = img_pat.findall(text)
    #print(title, text)
    slug = slug_date+'-'+slugify(umlaute(title.lower()))
    teaser = article['excerpt']

    i = 0
    for small_image in images_html:
        big_image = img_org.sub('', small_image).replace("www.", "").replace("blog.", "weitweg.")
        img_ext = os.path.splitext(small_image)[1].lower()
        if i == 0:
            new_image_name = slug + img_ext
        else:
            new_image_name = slug+'-' + str(i) + img_ext
        i = i + 1
        new_image_html = '/media/blog/' + new_image_name
        if image is None:
            image = 'blog/' + new_image_name

        html_image = {
            'url': big_image,
            'url2': small_image,
            'name': new_image_name
        }
        text = text.replace(small_image, new_image_html)
        images.append(html_image)

    print(image)

    elem = {
        'title_de': title,
        'text_de': text,
        'image': image,
        #'img_alt_de': '',
        'added': dt,
        'updated': dt,
        'published': dt,
        'range': 'global',
        'teaser_de': teaser,
        'host': None,
        "project": None,
        "author": None,
        "author_str": user,
    }

    post = {
        "model": "wbcore.blogpost",
        "pk": None,
        "fields": elem
    }

    post_list.append(post)

post_list.sort(key=lambda x: x['fields']['published'], reverse=False)

with open(filename, 'w') as outfile:
    json.dump(post_list, outfile)


for i, image in enumerate(images):
    url = image['url']
    name = image['name']

    filename = 'blog_images' + '/' + name.strip()

    if os.path.isfile(filename):
        print(filename, 'already exists. skip.')
        continue

    print('Download image ', i, 'from', len(images), ':', url, 'to blog_images/'+name)
    try:
        with request.urlopen(url) as response, open(filename, 'wb') as img_file:
            shutil.copyfileobj(response, img_file)
    except error.HTTPError:
        print("Could not download the image ", url)
        #### todo download images
        #styles/presselogo_custom_user_normal_1x/public
    except error.URLError:
        print("Could not download the image ", url)
    except UnicodeEncodeError:
        print("Could not read the image url.")
    except ValueError:
        print("Some value error.")

