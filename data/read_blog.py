#!/user/bin/python

import json
import sys
import datetime
import urllib.request
from slugify import slugify
import os
import getpass
import pymysql
import paramiko
import pandas as pd
from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder
from os.path import expanduser

filename = sys.argv[1]
pw = getpass.getpass()
user = getpass.getuser()


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
downloads = []

for index, article in df.iterrows():
    dt = pd.to_datetime(article['date'], format="%Y-%m-%d %H:%M:%S.%f").tz_localize('UTC').strftime("%Y-%m-%d %H:%M:%S.%f")
    print(dt)
    host = None
    user = article['display_name']

    #img = article['teaserimage']['src']
    slug = slugify(article['title'].rstrip())
    #img_ext = os.path.splitext(img)[1].lower()

    #download = {
    #    'url': img,
    #    'name': slug + img_ext
    #}

    #downloads.append(download)

    elem = {
        'title_de': article['title'].rstrip(),
        'text_de': article['content'].rstrip(),
        # 'image': "posts/"+download['name'],
        # 'img_alt_de': article['teaserimage']['alt'],
        'added': dt,
        'updated': dt,
        'published': dt,
        'range': 'global',
        'teaser_de': article['excerpt'],
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


def download(url, dname):
    urllib.request.urlretrieve(url, dname)

#for dl in downloads:
#    download(dl['url'], "images/" + dl['name'])
