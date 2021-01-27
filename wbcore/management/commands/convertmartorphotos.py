from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.core.files import File
from wbcore.models import NewsPost, BlogPost, Content, Document, Event, Partner, Project, Team, Photo
import datetime
import time
import re
import os
from weitblick import settings
from slugify import slugify

from django.db import transaction

class Command(BaseCommand):
    """
    Crawl all news models (except imported news and posts) for uploaded photos in the TextFields.
    Create a photologue photo object for each upload and change the corresponding url in the TextField.
    """
    def handle(self, *args, **options):
        modelfields = [
                       #(NewsPost, ["text", "teaser"]),
                       #(BlogPost, ["text", "teaser"]),
                       #(Content, ["text"]),
                       #(Document, ["description"]),
                       #(Event, ["description", "teaser"]),
                       #(Partner, ["description"]),
                       #(Project, ["description", "short_description"]),
                       (Team, ["description", "teaser"])
        ]

        for Model, fields in modelfields:
            self.convertphotosofmodel(Model, fields)

    def convertphotosofmodel(self, Model, fields):
        objs = Model.objects.all()
        if Model == NewsPost:
            objs = objs.filter(published__date__gte=datetime.date(2019, 11, 26))
        elif Model == BlogPost:
            objs = objs.filter(published__date__gte=datetime.date(2019, 12, 11))

        for obj in objs:
            self.convertphotosofentry(obj, fields, Model)

    def convertphotosofentry(self, obj, fields, Model):
        for field in fields:
            try:
                for lang in ['_de', '_en', '_es', '_fr']:
                    langfield = field + lang
                    self.updatetext(langfield, Model, obj)
            except:
                self.updatetext(field, Model, obj)

    def updatetext(self, fieldname, Model, obj):
        text = getattr(obj, fieldname)
        links = self.findurlintext(text)
        if links:
            for link in links:
                print(self.createphotologuepic(link[1], link[0], Model, obj))

    def findurlintext(self, text):
        #p = re.compile(r'!\[[^\]]*\]\(/media/images/uploads/[^)]*\)')
        p = re.compile(r"!\[([^\]]*)\]\(/(media/images/uploads/[^\)\'\"\s]*)([^\)]*)\)")
        return p.findall(text)

    def createphotologuepic(self, url, name, Model, obj):
        if Model == NewsPost:
            mytype = 'news'
        elif Model == BlogPost:
            mytype = 'blog'
        elif Model == Event:
            mytype = 'event'
        elif Model == Project:
            mytype = 'project'
        else:
            mytype = None

        try:
            user = getattr(obj, 'author')
        except AttributeError:
            user = None

        try:
            updated_time = obj.updated
        except AttributeError:
            updated_time = datetime.date.today()
        myname = '{} Texteditor Upload {}'.format(updated_time.strftime("%Y-%m-%d"), name)

        imagepath = os.path.join(settings.ENV_PATH, url)
        imageobj = File(open(imagepath, 'rb'))
        imageobj.name = myname

        hosts = obj.get_hosts()
        if len(hosts) == 1:
            host = hosts[0]
        else:
            host = None
        try:
            photo_obj = Photo(type=mytype, uploader=user, image=imageobj, title=myname, slug=slugify(myname), host=host)
            photo_obj.save()
        except IntegrityError:
            return Photo.objects.get(title=myname).image.url
        return photo_obj.image.url

    def converturltofilepath(self):
        raise NotImplementedError
