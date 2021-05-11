from django.core.management.base import BaseCommand
from wbcore.models import NewsPost, BlogPost
import datetime
from django.db import transaction

class Command(BaseCommand):
    """
    Add the host to the imported Photos which are used in the blog and news posts.
    Set the first photo of each post as title image.
    To Update query is hard becuse of the many-to-many relation, thus they are save in an atomic transaction.
    """

    def handle(self, *args, **options):
        for Model, date in zip([NewsPost, BlogPost], [datetime.date(2019, 11, 26), datetime.date(2019, 12, 11)]):
            self.addhosttomodelinstances(Model, date)

    def addhosttomodelinstances(self, Model, date):
        posts = Model.objects.filter(published__date__lte=date).exclude(photos=None).prefetch_related('photos')
        try:
            with transaction.atomic():
                for post in posts:
                    host = post.host
                    for pic in post.photos.all():
                        if pic.host is None:
                            pic.host = host
                            pic.save()
                    if post.image is None:
                        try:
                            title_image = post.photos.filter(title__endswith='-1')[0]
                            post.image = title_image
                            post.save()
                        except IndexError:
                            print('No photo found for {}'.format(post.title))
        except Exception as e:
            print(e)
        print(posts.count())
