from django.core.management.base import BaseCommand, CommandError
from wbcore.models import BlogPost, Host, Photo, NewsPost
import re
import json
import sys
import urllib.request
from slugify import slugify
import os
import datetime
from urllib import request, error
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

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
    users = {}

    def add_arguments(self, parser):
        parser.add_argument('news-file', nargs=1, type=str)
        parser.add_argument('user-file', nargs=1, type=str)

    def handle(self, *args, **options):
        news_file = options['news-file']
        user_file = options['user-file']

        print(news_file, user_file)

        with open(user_file[0]) as f:
            self.user_data = json.load(f)
            self.users = Command.parse_user_data(self.user_data)

        with open(news_file[0]) as f:
            self.news_data = json.load(f)
            self.parse_news_data(self.news_data)

    @staticmethod
    def umlaute(value):
        replacements = [(u'ä', u'ae'), (u'ü', u'ue'), (u'ö', u'oe'), (u'gesamtverein', u'bundesverband')]
        for (s, r) in replacements:
            value = value.replace(s, r)
        return value

    @staticmethod
    def parse_user_data(user_data):
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
        return users

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

    def parse_news_data(self, news_data):
        for article in news_data["news-list"]:
            article = article['news-article']

            dt = datetime.datetime.strptime(article['datetime'], "%Y-%m-%d %H:%M:%S")
            if dt < self.oldest:
                continue

            slug_date = dt.strftime("%Y-%m-%d")

            host_slug = article['wb-host'].lower()
            host_slug = Command.umlaute(host_slug)
            if host_slug in self.skip_citys:
                continue

            user_id = article['Autor']
            user = self.users[user_id]['name']
            host = Host.objects.get(slug=host_slug)
            title = article['article-title'].strip()
            text = article['article-text'].strip()
            teaser = article['conclusion'].strip()
            image = article['teaserimage']['src'].strip()
            slug = slug_date+'-'+slugify(self.umlaute(title.lower()))

            if not title:
                print("############## TITLE is not set... continue with next blog entry...")
                continue

            try:
                post = NewsPost.objects.get(slug=slug)
                continue
            except:
                post = NewsPost(title=title, slug=slug, text=text, text_de=text, added=dt,
                            updated=dt, published=dt, range='global', teaser=teaser,
                            teaser_de=teaser, host=host, author_str=user)
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

            photo = self.get_photo(image, dt, title)
            if photo:
                post.photos.add(photo)  # add teaser image

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
            img_temp.write(urllib.request.urlopen(image_url).read())
            img_temp.flush()

            try:
                photo = Photo.objects.get(title=title, slug=slug)
            except:
                photo = Photo(title=title, slug=slug, caption=caption, date_added=date, type='news')
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
                request.urlopen(new_url)
                return new_url, filename, ext
            except UnicodeEncodeError:
                try:
                    new_url = path + "/" + request.quote(filename) + "." + ext
                    req = urllib.request.Request(new_url)
                    req.get_method = lambda: 'HEAD'
                    request.urlopen(new_url)
                    return new_url, filename, ext
                except error.HTTPError:
                    continue
            except error.HTTPError:
                continue
            except error.URLError:
                return None, None, None
            except ValueError:
                return None, None, None

        return None, None, None

