from django.core.management.commands.dumpdata import Command as DumpDataCommand


class Command(DumpDataCommand):

    data = [('wbcore.address', 'address.json'),
            ('wbcore.location', 'locations.json'),
            ('wbcore.host', 'hosts.json'),
            ('photologue', 'images.json'),
            ('wbcore.newspost', 'news.json'),
            ('wbcore.blogpost', 'blog.json'),
            ('wbcore.partner', 'partner.json'),
            ('schedule', 'schedule.json'),
            ('form_designer.form', 'forms.json'),
            ('wbcore.event', 'events.json'),
            ('wbcore.project', 'projects.json'),
            ]

    def handle(self, *app_labels, **options):

        folder = 'data/'

        for model in self.data:
            app_labels = [model[0], ]
            options['output'] = folder + model[1]
            # override options, app_labels and code method

            print("writing ", model[0], "to", options['output'], "...")
            super(Command, self).handle(*app_labels, **options)
