import getpass

import pandas as pd
import pymysql
from django.core.management.base import BaseCommand, CommandError
from wbcore.models import BlogPost, Host, Photo
import re
import json
import sys
import urllib.request
from slugify import slugify
import os
import datetime
from sshtunnel import SSHTunnelForwarder
from urllib import request, error
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import ssl


#Create new ssl context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
httpsHandler = urllib.request.HTTPSHandler(context = ctx)

sslcontext = ssl.create_default_context()
class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    sql_hostname = 'localhost'
    sql_username = 'root'
    sql_password = None
    sql_main_database = 'weitweg-blog'
    sql_port = 3306

    ssh_host = 'weitblicker.org'
    ssh_user = 'spuetz'
    ssh_port = 22
    ssh_pw = None

    df = None

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



    oldest = datetime_object = datetime.datetime.strptime('2008-01-01', '%Y-%m-%d')
    skip_citys = ['tuebingen']

    image_extensions = ['jpg', 'jpeg', 'JPG', 'JPEG', 'png', 'PNG', 'gif', 'GIF']

    img_org = re.compile(r'(-\d+x\d+)')
    img_pat = re.compile(r'<img [^>]*src="(?P<src>.+?)".+?>')
    caption_img = re.compile(r'\[caption.*?caption="(?P<caption>.*?)".*?\].*?<img [^>]*src="(?P<src>[^"]+).*?\[/caption\]')
    video_pat = re.compile(r'\[video.*?[mp4|src]="(?P<src>.+?)".*?\](?:.*?\[/video\])?')
    tag_pat = re.compile(r'\[.*?\](?:.*?\[.*?\])?')
    link_pat = re.compile(r'href="([^"]+)')
    p_tag_pat = re.compile(r'(<p>.+?</p>)|(<img.+?src=".+?".*?>)')
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    rmnewlines = re.compile(r'\n\s*\n')

    news_data = None
    user_data = None

    news_default = None

    slugs = {}
    titles = {}

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        pw = getpass.getpass()
        self.ssh_pw = pw
        self.sql_password = pw
        #self.ssh_user = getpass.getuser()

        with SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_password=self.ssh_pw,
                remote_bind_address=(self.sql_hostname, self.sql_port)) as tunnel:
            conn = pymysql.connect(host='127.0.0.1', user=self.sql_username, passwd=self.sql_password,
                                   db=self.sql_main_database, port=tunnel.local_bind_port)
            df = pd.read_sql_query(self.query, conn)
            conn.close()

            self.parse_news_data(df)

    @staticmethod
    def umlaute(value):
        replacements = [(u'ä', u'ae'), (u'ü', u'ue'), (u'ö', u'oe'), (u'gesamtverein', u'bundesverband')]
        for (s, r) in replacements:
            value = value.replace(s, r)
        return value

    def make_slug(self, name):
        slug = slugify(self.umlaute(name.lower()))
        slug = slug[:100]
        if slug in self.slugs:
            self.slugs[slug] += 1
        else:
            self.slugs[slug] = 1

        return slug + '-' + str(self.slugs[slug])

    def make_title(self, name):
        if name in self.titles:
            self.titles[name] += 1
        else:
            self.titles[name] = 1

        return name + '-' + str(self.titles[name])

    def parse_news_data(self, df):

        for index, article in df.iterrows():

            ## read date time
            dt = pd.to_datetime(article['date'], format="%Y-%m-%d %H:%M:%S")
            slug_date = dt.strftime("%Y-%m-%d")
            #dt = dt_obj.tz_localize('UTC').strftime("%Y-%m-%d %H:%M:%S.%f")

            ## read host
            host = 'muenster'

            ## read user
            user = article['user_login']

            ## read content
            text = article['content']

            ## read title
            title = article['title']
            if not isinstance(title, str):
                title = title[0]
            title = title.strip()

            if not title:
                print("############## TITLE is not set... continue with next blog entry...")
                continue

            ## read teaser
            teaser = article['excerpt']

            ##
            slug = self.make_slug(title)

            ## read gallery

            gallery_raw = article['gallery']
            gallery = []
            if gallery_raw is not None:
                gallery_raw = gallery_raw.split(';%')
                for entry in gallery_raw:
                    try:
                        g_photo_url, g_photo_date, g_photo_title = entry.split(',%')
                        g_photo_date = pd.to_datetime(g_photo_date, format="%Y-%m-%d %H:%M:%S")
                        gallery.append({
                            'url': g_photo_url,
                            'date': g_photo_date,
                            'title': g_photo_title,
                        })
                    except:
                        g_photo_entry = entry.split(',%')
                        if len(g_photo_entry) > 0:
                            for ext in self.image_extensions:
                                if g_photo_entry[0].endswith(ext):
                                    gallery.append({
                                        'url': g_photo_entry[0],
                                        'date': dt,
                                        'title': "",
                                    })
                                    break
                        else:
                            print("Exception: Gallery string does not consists out of three values:", entry.split(',%'))


            tags = self.caption_img.findall(text)

            try:
                post = BlogPost.objects.get(slug=slug)
                continue
            except BlogPost.DoesNotExist:
                post = BlogPost(title=title, slug=slug, text=text, text_de=text, added=dt,
                            updated=dt, published=dt, range='global', teaser=teaser,
                            teaser_de=teaser, host=Host.objects.get(slug=host), author_str=user)
            post.save()

            def sub_image_match(match):
                gd = match.groupdict()
                caption = gd['caption'] if 'caption' in gd else ""
                image = gd['src']
                image = self.img_org.sub('', image)
                photo = self.get_photo(image, dt, title, caption)  # add teaser image
                if photo:
                    post.photos.add(photo)
                    return '![%s](%s "%s")' % (photo.title, photo.image.url, photo.title)
                return ""  # remove from html and just add link to photologue object

            for elem in gallery:
                img_title = elem['title'] if elem['title'] else title # if image has title use it, else use article title
                photo = self.get_photo(title=img_title, date=elem['date'], image=elem['url'])
                if photo:
                    post.photos.add(photo)

            text = self.caption_img.sub(sub_image_match, text)
            text = self.img_pat.sub(sub_image_match, text)
            text = re.sub(self.cleanr, '', text)
            text = re.sub(self.rmnewlines, '\n\n', text)

            post.text = text
            post.text_de = text
            #text = video_pat.sub(new_video_html, text)
            #tags = tag_pat.findall(text)
            post.save()

    def get_photo(self, image, date, title, caption=""):

        image = image.replace("www.", "").replace("blog.", "weitweg.")
        image = re.sub(r'styles/.*?/public/', '', image)
        image = re.sub(r'\?.*', '', image)

        if "neues-default" in image:
            return None

        image_url, name, ext = self.alter_file_extension(image)

        if image_url:
            slug = self.make_slug(date.strftime("%Y-%m-%d") + '-' + title)
            title = self.make_title(title)

            new_name = "%s.%s" % (slug, ext)
            print("image name:", new_name)

            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urllib.request.urlopen(image_url, context=ctx).read())
            img_temp.flush()

            try:
                photo = Photo.objects.get(title=title, slug=slug)
            except:
                photo = Photo(title=title, slug=slug, caption=caption, date_added=date, type='blog')
                photo.image.save(new_name, File(img_temp))
                photo.save()
            return photo

        else:
            print("Could not open url:", image_url)
            return None

    def alter_file_extension(self, url):

        path_parts = url.split("/")
        full_filename = path_parts[-1]
        path = "/".join(path_parts[0:-1])
        filename = full_filename.split(".")[0]

        for ext in self.image_extensions:
            new_url = path + "/" + filename + "." + ext
            try:
                req = urllib.request.Request(new_url)
                req.get_method = lambda: 'HEAD'
                request.urlopen(new_url, context=ctx)
                return new_url, filename, ext
            except UnicodeEncodeError:
                try:
                    new_url = path + "/" + request.quote(filename) + "." + ext
                    req = urllib.request.Request(new_url)
                    req.get_method = lambda: 'HEAD'
                    request.urlopen(new_url, context=ctx)
                    return new_url, filename, ext
                except error.HTTPError as http_error:
                    print("HTTPError:", http_error)
                    continue
            except error.HTTPError as http_error:
                print("HTTPError:", http_error)
                continue
            except error.URLError as url_error:
                print("URLError:", url_error)
                return None, None, None
            except ValueError as value_error:
                print("ValueError:", value_error)
                return None, None, None

        return None, None, None

