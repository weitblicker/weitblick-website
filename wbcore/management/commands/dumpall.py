from django.core.management.commands.dumpdata import Command as DumpDataCommand


class Command(DumpDataCommand):

    data = [('wbcore.location', 'locations.json'),
            ('wbcore.event', 'events.json'),
            ('schedule', 'schedule.json')]

    def handle(self, *app_labels, **options):

        folder = 'data/'

        for model in self.data:
            app_labels = [model[0], ]
            options['output'] = folder + model[1]
            # override options, app_labels and code method

            print("writing ", model[0], "to", options['output'], "...")
            super(Command, self).handle(*app_labels, **options)
