from django.core.management.base import BaseCommand
from wbcore.models import NewsPost, BlogPost, Content, Document, Event, Partner, Project, Team, Photo
import datetime
import re
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
                       (Event, ["description", "teaser"]),
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
            self.convertphotosofentry(obj, fields)

    def convertphotosofentry(self, obj, fields):
        for field in fields:
            try:
                for lang in ['_de', '_en', '_es', '_fr']:
                    langfield = field + lang
                    text = getattr(obj, langfield)
                    self.updatetext(text)
            except:
                text = getattr(obj, field)
                self.updatetext(text)

    def updatetext(self, text):
        self.findurlintext(text)

    def findurlintext(self, text):
        p = re.compile(r'!\[[^\]]*\]\(/media/images/uploads/[^)]*\)')
        print(p.findall(text))

    def createphotologuepic(self, url):
        return None


