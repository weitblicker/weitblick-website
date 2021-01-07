from django.core.management.base import BaseCommand
from wbcore.models import Host
from fixture_magic.management.commands.dump_object import Command as DumpObjectCommand
import io
import sys
import os
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
            #('wbcore.event', {"hosts__slug": host.slug}),
        ]

        # backup

        dump_folder = f'data/{host.slug}/'
        if not os.path.exists(dump_folder):
            os.makedirs(dump_folder)

        for model, query in models:
            print(model, query)
            temp_stdout = io.StringIO()
            sys.stdout = temp_stdout
            DumpObjectCommand().handle(model=model, ids=None, query=json.dumps(query))
            with open(dump_folder + model.split('.')[-1] + '.json', 'w') as f:
                f.write(temp_stdout.getvalue())
            sys.stdout = sys.__stdout__
            print(temp_stdout.getvalue())

        # save documents and files

        # delete

        for model, query in models:
            if model == 'wbcore.host':  # do not delete host, but set as dissolved
                host.dissolved = True
                #host.save()
            else:
                pass

        print(host.name + ' dissolved')