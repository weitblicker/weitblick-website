from django.core.management.base import BaseCommand
from wbcore.models import Host
from django.template import loader
from django.conf import settings
from zipfile import ZipFile
import os
import codecs
from cairosvg import svg2png
from copy import copy


class Command(BaseCommand):
    """Create set of logos for a city or all cities"""
    def handle(self, *args, **options):
        if options['city']:
            host_slug = options['city']
            try:
                host = Host.objects.get(slug=host_slug)
            except Host.DoesNotExist:
                raise ValueError('The host \'{}\' could not be found. Please provide the slug of an existing host.'.format(host_slug))
            self.create_logo(host)
        else:
            for host in Host.objects.all():
                self.create_logo(host)




    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super(Command, self).create_parser(prog_name, subcommand, **kwargs)
        parser.add_argument('-c', '--city', help='slug of the weitblick city/host you want to create the logo for')
        return parser


    def create_logo(self, host):
        print('creating logos for {}'.format(host.slug))

        template = loader.get_template('wbcore/svgs/logo_standalone.svg')
        path = "%(media_root)slogos/%(slug)s/%(name)s.%(ext)s"

        logo_black = '#04090e'
        logo_orange = '#f3971b'
        logo_grey = '#969696'
        logo_white = '#ffffff'

        color_map = {
            # text, weitblick, puzzle
            'standard': (logo_grey, logo_black, logo_orange),
            'grey': (logo_grey, logo_black, logo_grey),
            'grey_negative': (logo_grey, logo_white, logo_grey),
            'black': (logo_black, logo_black, logo_black),
            'white': (logo_white, logo_white, logo_white)
        }

        dpi_list = [72, 150, 300]
        width = 350  # 386.76
        height = 125  # 141.55

        zip_path = path % dict(media_root=settings.MEDIA_ROOT, slug=host.slug, name="%s_%s" % ("logos", host.slug),
                               ext="zip")

        if not os.path.exists(os.path.dirname(zip_path)):
            try:
                os.makedirs(os.path.dirname(zip_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        zip_obj = ZipFile(zip_path, "w")

        for key, colors in color_map.items():
            svg_name = "logo_%s_%s" % (host.slug, key)
            svg_path = path % dict(media_root=settings.MEDIA_ROOT, slug=host.slug, name=svg_name, ext="svg")

            svg_logo = template.render(
                {'text': 'Bildungschancen weltweit!' if host.slug == 'bundesverband' else host.city.upper(),
                 'title_text': host.city,
                 'color_text': colors[0],
                 'color_weitblick': colors[1],
                 'color_puzzle': colors[2]
                 })

            with codecs.open(svg_path, 'w', encoding='utf8') as file:
                file.write(svg_logo)

            zip_obj.write(svg_path, os.path.basename(svg_path))

            for dpi in dpi_list:
                try:
                    name = "logo_%s_%s_%sdpi" % (host.slug, key, dpi)
                    png_path = path % dict(media_root=settings.MEDIA_ROOT, slug=host.slug, name=name, ext="png")

                    svg2png(bytestring=svg_logo, write_to=png_path, dpi=dpi, output_width=round(width * dpi / 72),
                            output_height=round(height * dpi / 72))

                    zip_obj.write(png_path, os.path.basename(png_path))
                except OSError as exception:
                    print("Could not convert logo file %s, Exception %s" % (svg_path, exception))

        zip_obj.close()