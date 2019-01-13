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
from urllib.parse import quote

blog_filename = sys.argv[1]
photos_filename = sys.argv[2]

pw = getpass.getpass()
user = getpass.getuser()

img_pat = re.compile(r'<img [^>]*src="(?P<src>.+?)".+?>')
caption_img = re.compile(r'\[caption.*?caption="(?P<caption>.*?)".*?\].*?<img [^>]*src="(?P<src>[^"]+).*?\[/caption\]')
video_pat = re.compile(r'\[video.*?[mp4|src]="(?P<src>.+?)".*?\](?:.*?\[/video\])?')
tag_pat = re.compile(r'\[.*?\](?:.*?\[.*?\])?')
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

query = '''select p.ID, p.post_title as title, p.post_excerpt as excerpt, p.post_content as content, p.post_date as 'date', p.post_date_gmt as date_gmt, u.user_login, u.display_name, u.ID as user_id, u.user_email, t.name as country, GROUP_CONCAT(p2.Tag) as tags, GROUP_CONCAT(DISTINCT CONCAT(image_url,',% ', image_date,',% ', image_title) SEPARATOR ';%') as gallery, p.guid as old_page from wp_posts p 
left join wp_users u on p.post_author=u.ID 
inner join wp_term_relationships r on r.object_id=p.ID
inner join wp_term_taxonomy tax on r.term_taxonomy_id=tax.term_taxonomy_id
inner join wp_terms t on tax.term_id=t.term_id
left join (select p2.ID, t2.name as Tag from wp_posts p2 inner join wp_term_relationships r2 on r2.object_id=p2.ID
inner join wp_term_taxonomy tax2 on r2.term_taxonomy_id=tax2.term_taxonomy_id
inner join wp_terms t2 on tax2.term_id=t2.term_id where tax2.taxonomy = 'post_tag' ) p2 on p2.ID=p.ID
left join (select i.post_date_gmt as image_date, i.post_content as image_title, i.post_parent, i.post_type, i.guid as image_url from wp_posts i where i.post_type = 'attachment') p3 on p3.post_parent=p.ID 
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

photo_list = {}
post_list = []
gallery_list = []
images = []
photo_pk = 0
gallery_pk = 0
photologue_list = []
all_slugs = {}
all_titles = {}
all_galleries = {}

def make_slug(name):
    slug = slugify(umlaute(name.lower()))
    slug = slug[:100]
    if slug in all_slugs:
        all_slugs[slug] += 1
    else:
        all_slugs[slug] = 1
    
    return slug + '-' + str(all_slugs[slug])


def make_title(name):

    if name in all_titles:
        all_titles[name] += 1
    else:
        all_titles[name] = 1
    
    return name + '-' + str(all_titles[name])


def make_gallery_title(name):

    if name in all_galleries:
        all_galleries[name] += 1
    else:
        all_galleries[name] = 1
    
    return name + '-' + str(all_galleries[name])


def add_new_gallery(date, title, slug, desc, photos):

    fields ={
        "date_added": date,
        "title": make_gallery_title(title),
        "slug": slug,
        "description": desc,
        "is_public": True,
        "photos": photos,
        "sites": [1]
    }

    global gallery_pk
    gallery_list.append({
        "model": "photologue.gallery",
        "pk": gallery_pk,
        "fields": fields
    })

    gallery_pk += 1
    return gallery_pk-1



for index, article in df.iterrows():

    dt_obj = pd.to_datetime(article['date'], format="%Y-%m-%d %H:%M:%S")
    slug_date = dt_obj.strftime("%Y-%m-%d")
    dt = dt_obj.tz_localize('UTC').strftime("%Y-%m-%d %H:%M:%S.%f")

    host = None
    user = article['user_login']
    text = article['content']
    title = article['title']
    gallery_raw = article['gallery']
    gallery = []
    if gallery_raw is not None:
        gallery_raw = gallery_raw.split(';%')
        for entry in gallery_raw:
            try:
                g_photo_url, g_photo_date, g_photo_title = entry.split(',%')
                gallery.append({
                    'url' : g_photo_url,
                    'date': g_photo_date,
                    'title': g_photo_title,
                })
            except:
                g_photo_entry = entry.split(',%')
                if len(g_photo_entry) > 0 and (g_photo_entry[0].endswith(".jpg") or g_photo_entry[0].endswith(".jpeg")):
                    gallery.append({
                        'url' : g_photo_entry[0],
                        'date': dt,
                        'title': "",
                    })
                else:
                    print("Exception: Gallery string does not consists out of three values:", entry.split(',%'))              

    if not isinstance(title, str):
        title = title[0]
    else:
        article['title']

    title = title.strip()

    if not title:
        print("############## TITLE is not set... continue with next blog entry...")
        continue

    teaser_image = None
    teaser_image_caption = ""
    tags = caption_img.findall(text)

    photos=[]
    
 #   if tags:
 #       for tag in tags:
 #           print(tag)

    #print(title, text)
    slug = slug_date+'-'+slugify(umlaute(title.lower()))
    teaser = article['excerpt']

    video_html = '<video width="400" controls><source src="{0}" type="video/mp4">Your browser does not support HTML5 video.</video>'

    def new_video_html(match):
        link = match.group(1)
        #print("Found video:", link)

        video_ext = os.path.splitext(link)[1].lower()
        new_video_name = slug + video_ext
        new_video_link = '/media/blog/' + new_video_name

        video_info = {
            'url': link,
            'name': new_video_name     
        }

        images.append(video_info)
        tmp = video_html.format(new_video_link)
        #print(tmp)
        return tmp

    i = 0

    def sub_image_match(match):

        gd = match.groupdict()
        caption = gd['caption'] if 'caption' in gd else ""
        image = gd['src']
        image = img_org.sub('', image)

        #print("Found image:", image)
        #if caption != "": print("With caption:", caption)

        add_image(image, dt, caption)
        return "" # remove from html and just add link to photologue object


    def add_image(image, date, caption = "", special_title=None):

        image = image.replace("www.", "").replace("blog.", "weitweg.")

        img_slug = ""
        img_title = ""

        if special_title is not None:
            special_title = special_title.strip()

        if special_title:
            img_slug = make_slug(slug_date + '-' + special_title)
            img_title = make_title(special_title)
        else:
            img_slug = make_slug(slug_date + '-' + title)
            img_title = make_title(title)


        #print("slug:",img_slug, "title:", special_title)
        #if img_title is "":
        #    print("############## IMG TITLE is not set")
            
        ext = os.path.splitext(image)[1].lower()
        new_name = img_slug + ext
        new_link = 'images/photos/' + new_name

        global teaser_image, teaser_image_caption
        if not teaser_image:
            teaser_image = new_link
            teaser_image_caption = caption


        image_field = {
            "image": new_link,
            "date_taken": None,
            "view_count": 0,
            "crop_from": "center",
            "effect": None,
            "title": img_title,
            "slug": img_slug,
            "caption": caption,
            "date_added": date.strip(),
            "is_public": True,
            "sites": [1]
        }

        global photo_pk
        photo = {
            "model": "photologue.photo",
            "pk": photo_pk,
            "fields": image_field,
        }

        if image in photo_list:
            photo = photo_list[image]
        else:
            photo_list[image] = photo
            images.append({
                'url': image,
                'name': new_name     
            })
            photo_pk += 1
        photos.append(photo['pk'])

    
    text = caption_img.sub(sub_image_match, text)

    text = img_pat.sub(sub_image_match, text)

    for entry in gallery:
        # path date title
        add_image(entry['url'], entry['date'], "", entry['title'])

    text = video_pat.sub(new_video_html, text)  

    tags = tag_pat.findall(text)

    #for tag in tags:
    #    print(tag, title)

    current_gallery_pk = None
    if len(photos) > 1:
        current_gallery_pk = add_new_gallery(dt, title, slug, "", photos)

    elem = {
        'title_de': title,
        'text_de': text,
        'image': teaser_image,
        'img_alt_de': teaser_image_caption,
        'added': dt,
        'updated': dt,
        'published': dt,
        'range': 'global',
        'teaser_de': teaser,
        'host': None,
        "project": None,
        "author": None,
        "author_str": user,
        "gallery": current_gallery_pk,
    }

    post = {
        "model": "wbcore.blogpost",
        "pk": None,
        "fields": elem
    }

    post_list.append(post)

post_list.sort(key=lambda x: x['fields']['published'], reverse=False)

print("Write json files...")
with open(blog_filename, 'w') as outfile:
    json.dump(post_list, outfile)


photologue_list.extend(photo_list.values())
photologue_list.extend(gallery_list)

with open(photos_filename, 'w') as outfile:
    json.dump(photologue_list, outfile)


def alter_file_extension(url):
    extensions = ['jpg', 'jpeg', 'JPG', 'JPEG', 'png', 'PNG', 'gif', 'GIF']

    path_parts = url.split("/")
    fullfilename = path_parts[-1]
    path = "/".join(path_parts[0:-1])
    filename = fullfilename.split(".")[0]

    for ext in extensions:
        new_url = path + "/" + filename + "." + ext
        #print("Trying:", new_url)
        try:
            req = urllib.request.Request(new_url)
            req.get_method = lambda: 'HEAD'
            request.urlopen(new_url)
            #print("Found alternative URL:", new_url)
            return new_url
        except UnicodeEncodeError:
            try:
                new_url = path + "/" + request.quote(filename) + "." + ext
                req= urllib.request.Request(new_url)
                req.get_method = lambda: 'HEAD'
                request.urlopen(new_url)
                #print("Found alternative URL:", new_url)
                return new_url
            except error.HTTPError:
                continue
        except error.HTTPError:
            continue
        except error.URLError:
            return ""
        except ValueError:
            return ""

    return ""

print("Download media files...")
for i, image in enumerate(images):
    url = image['url']
    original_url = url
    name = image['name']

    filename = 'blog_images' + '/' + name.strip()

    if ".mp4" in url:
        print(url)

    print("Download:", filename)
    if os.path.isfile(filename):
        try:
            site = request.urlopen(url)
        except:
            url = alter_file_extension(url)
            if url != "":
                site = request.urlopen(url)
            else:
                #print("Could not open URL:", url, "skipping it...")
                continue
        server_file_length = int(site.info()["Content-Length"])
        f = open(filename, "rb")
        disk_file_length = len(f.read())
        f.close()

        if server_file_length == disk_file_length:
            print("File already exists:", filename, "skip.")
            continue
        else:
            print("Found broken file. Server Content-Length:", server_file_length,
             "Disk Content-Length:", disk_file_length, "Downloading it again...");

    try:
        with request.urlopen(url) as response, open(filename, 'wb') as img_file:
            print('Download image ', i, 'from', len(images), ':', url, 'to blog_images/'+name)
            shutil.copyfileobj(response, img_file)
    except:
        url = alter_file_extension(url)
        if url != "":
            #print("Download from alternative URL:", url, "...")
            try:
                with request.urlopen(url) as response, open(filename, 'wb') as img_file:
                    print('Download image ', i, 'from', len(images), ':', url, 'to blog_images/'+name)
                    print("Download from alternative URL:", url, "...")
                    shutil.copyfileobj(response, img_file)
            except error.HTTPError:
                print("HTTPError: Could not download the image ", url)
            except error.URLError:
                print("URLError: Could not download the image ", url)
            except UnicodeEncodeError:
                print("UnicodeEncodeError: Could not read the image url.")
            except ValueError:
                print("Some value error.")
        else:
            #print("File under the URL", original_url, "does not exist!")
            continue;

