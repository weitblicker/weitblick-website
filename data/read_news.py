#!/user/bin/python

import re
import json
import sys
import urllib.request
from slugify import slugify
import os
import datetime
from urllib import request, error
import shutil
import time


raw_news_filename = sys.argv[1]
raw_user_filename = sys.argv[2]
news_filename = sys.argv[3]
photos_filename = sys.argv[4]

photo_pk = 0
gallery_pk = 0

try:
    photo_pk = int(sys.argv[5])
    gallery_pk = int(sys.argv[6])
except:
    photo_pk = 0
    gallery_pk = 0

img_pat = re.compile(r'<img [^>]*src="(?P<src>.+?)".+?>')
caption_img = re.compile(r'\[caption.*?caption="(?P<caption>.*?)".*?\].*?<img [^>]*src="(?P<src>[^"]+).*?\[/caption\]')
video_pat = re.compile(r'\[video.*?[mp4|src]="(?P<src>.+?)".*?\](?:.*?\[/video\])?')
tag_pat = re.compile(r'\[.*?\](?:.*?\[.*?\])?')
img_org = re.compile(r'(-\d+x\d+)')
link_pat = re.compile(r'href="([^"]+)')
p_tag_pat = re.compile(r'(<p>.+?</p>)|(<img.+?src=".+?".*?>)')

def umlaute(value):
    replacements = [(u'ä', u'ae'), (u'ü', u'ue'), (u'ö', u'oe'), (u'gesamtverein', u'bundesverband')]
    for (s, r) in replacements:
        value = value.replace(s, r)
    return value

photo_list = {}
news_list = []
gallery_list = []
images = []
photologue_list = []
all_slugs = {}
all_titles = {}
all_galleries = {}

with open(raw_news_filename) as f:
    data = json.load(f)

with open(raw_user_filename) as uf:
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

oldest = datetime_object = datetime.datetime.strptime('2008-01-01', '%Y-%m-%d')
skip_citys = ['tuebingen']

for article in data["news-list"]:
    article = article['news-article']
    dt_obj = datetime.datetime.strptime(article['datetime'], "%Y-%m-%d %H:%M:%S")

    if dt_obj < oldest:
        continue

    #dt = dt_obj.tz_localize('UTC').strftime("%Y-%m-%d %H:%M:%S.%f")
    dt = dt_obj.isoformat()

    slug_date = dt_obj.strftime("%Y-%m-%d")
    host = article['wb-host'].lower()
    host = umlaute(host)
    if host in skip_citys:
        print(host)
        continue

    user_id = article['Autor']
    user = users[user_id]['name']

    title = article['article-title'].strip()
    text = article['article-text'].strip()
    teaser = article['conclusion'].strip()
    image = article['teaserimage']['src'].strip()
    slug = slug_date+'-'+slugify(umlaute(title.lower()))

    if not title:
        print("############## TITLE is not set... continue with next blog entry...")
        continue

    teaser_image = None

    photos = []

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


    def add_image(image, date, caption="", special_title=None):

        image = image.replace("www.", "").replace("blog.", "weitweg.")
        image = re.sub(r'styles/.*?/public/', '', image)
        image = re.sub(r'\?.*', '', image)

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

        if "neues-default" in image:
            img_title = 'neues-default'


        #print("slug:",img_slug, "title:", special_title)
        #if img_title is "":
        #    print("############## IMG TITLE is not set")
            
        ext = os.path.splitext(image)[1].lower()
        new_name = img_slug + ext
        new_link = 'images/photos/' + new_name


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

        global teaser_image
        if not teaser_image:
            teaser_image = photo['pk']


    add_image(image, dt)    # add teaser image
    
    text = caption_img.sub(sub_image_match, text)

    text = img_pat.sub(sub_image_match, text)

    text = video_pat.sub(new_video_html, text)

    tags = tag_pat.findall(text)

    current_gallery_pk = None
    if len(photos) > 1:
        current_gallery_pk = add_new_gallery(dt, title, slug, "", photos)

    elem = {
        'title_de': title,
        'text_de': text,
        'image': teaser_image,
        'added': dt,
        'updated': dt,
        'published': dt,
        'range': 'global',
        'teaser_de': teaser,
        'host': host,
        "project": None,
        "author": None,
        "author_str": user,
        "gallery": current_gallery_pk,
    }

    post = {
        "model": "wbcore.newspost",
        "pk": None,
        "fields": elem
    }

    news_list.append(post)

news_list.sort(key=lambda x: x['fields']['published'], reverse=False)

print("Write json files...")
with open(news_filename, 'w') as outfile:
    json.dump(news_list, outfile, indent=4, sort_keys=True)


photologue_list.extend(photo_list.values())
photologue_list.extend(gallery_list)

with open(photos_filename, 'w') as outfile:
    json.dump(photologue_list, outfile, indent=4, sort_keys=True)


print("Next gallery pk:", gallery_pk)
print("Next photo pk:", photo_pk)

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

time.sleep(5)

print("Download media files...")
for i, image in enumerate(images):
    url = image['url']
    original_url = url
    name = image['name']

    filename = 'news_images' + '/' + name.strip()

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

