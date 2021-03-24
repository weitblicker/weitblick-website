from django.core.management.base import BaseCommand
from django.conf import settings
from wbcore.models import Host, Document, Photo, UserRelation
from wbcore.models import SocialMediaLink, JoinPage, Content, Event, NewsPost, BlogPost, Document, Team, Donation, ContactMessage
from fixture_magic.management.commands.dump_object import Command as DumpObjectCommand
from fixture_magic.management.commands.merge_fixtures import Command as MergeFixturesCommand
import io
import sys
import os
import shutil
import json

class Command(BaseCommand):
    """Delete a city permanently"""


    def add_arguments(self, parser):
        parser.add_argument('host_slug', type=str)

    def handle(self, *args, **options):
        host = Host.objects.get(slug=options["host_slug"])
        host.dissolved = False

        #confirm = input('Are you sure you want to dissolve the host "' + host.name + '"? This will delete a lot of data permanently! (yes/NO) ')
        #if confirm != 'yes':
        #    print('abort')
        #    return None


        models = [
            ('wbcore.host', {"pk__in": [host.slug]}),
            ('wbcore.newspost', {"host__slug": host.slug}),
            ('wbcore.blogpost', {"host__slug": host.slug}),
            ('wbcore.project', {"hosts__slug": host.slug}),
            ('wbcore.event', {"host__slug": host.slug}),
            ('wbcore.document', {"host__slug": host.slug}),
            # ('wbcore.external_document', {}),  # TODO not yet merged in master
            ('wbcore.content', {"host__slug": host.slug}),
            ('wbcore.team', {"host__slug": host.slug}),
            ('wbcore.donation', {"host__slug": host.slug}),
            ('wbcore.contactmessage', {"host__slug": host.slug}),
            ('wbcore.userrelation', {"host__slug": host.slug}),  # includes users
            ('wbcore.teamuserrelation', {'team__host__slug': host.slug}),
            ('wbcore.photo', {"host__slug": host.slug}),
        ]

        def get_model_filename(model_name, folder=''):
            return dump_folder + model_name.split('.')[-1] + '.json'

        # backup

        dump_folder = f'data/{host.slug}/'
        if not os.path.exists(dump_folder):
            os.makedirs(dump_folder)

        for model, query in models:
            temp_stdout = io.StringIO()
            sys.stdout = temp_stdout
            DumpObjectCommand().handle(model=model, ids=None, query=json.dumps(query))
            with open(get_model_filename(model, folder=dump_folder), 'w') as f:
                f.write(temp_stdout.getvalue())
            sys.stdout = sys.__stdout__

        # merge fixtures

        temp_stdout = io.StringIO()
        sys.stdout = temp_stdout
        files = [get_model_filename(model[0], folder=dump_folder) for model in models]
        MergeFixturesCommand().handle(*files)
        with open(dump_folder + f'{host.slug}.json', 'w') as f:
            f.write(temp_stdout.getvalue())
        sys.stdout = sys.__stdout__

        # save documents and photos

        for document in Document.objects.filter(host__slug=host.slug):
            os.makedirs(os.path.dirname(dump_folder + document.file.url.strip('/')), exist_ok=True)
            shutil.copyfile(document.file.path, dump_folder + document.file.url.strip('/'))

        for photo in Photo.objects.filter(host__slug=host.slug):
            os.makedirs(os.path.dirname(dump_folder + photo.image.url.strip('/')), exist_ok=True)
            shutil.copyfile(photo.image.path, dump_folder + photo.image.url.strip('/'))

        for user_relation in UserRelation.objects.filter(host__slug=host.slug):
            user = user_relation.user
            try:
                os.makedirs(os.path.dirname(dump_folder + user.image.url.strip('/')), exist_ok=True)
                shutil.copyfile(user.image.path, dump_folder + user.image.url.strip('/'))
            except ValueError:
                pass

        # delete

        # keep host itself, delete related objects
        # TODO check if this is everything
        SocialMediaLink.objects.filter(host=host).delete()
        JoinPage.objects.filter(host=host).delete()
        Content.objects.filter(host=host).exclude(type='welcome').delete()
        Event.objects.filter(host=host).delete()
        UserRelation.objects.filter(host=host).delete()
        NewsPost.objects.filter(host=host).delete()
        BlogPost.objects.filter(host=host).delete()
        Document.objects.filter(host=host).delete()
        Team.objects.filter(host=host).delete()
        Donation.objects.filter(host=host).delete()
        ContactMessage.objects.filter(host=host).delete()
        # keep projects
        Photo.objects.filter(host=host).exclude(type='project')
        # User? many to many -> only delete if

        host.dissolved = True
        host.save()

        print(host.name + ' dissolved')