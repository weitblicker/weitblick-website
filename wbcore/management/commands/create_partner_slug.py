from django.core.management.base import BaseCommand, no_translations
from wbcore.models import Partner
import slugify

class Command(BaseCommand):
    """
    Creates slugs based on the name for each partner without slug.
    """
    @no_translations
    def handle(self, *args, **options):
        slug_less_partners = Partner.objects.all().filter(slug__isnull=True)
        slug_list = list(Partner.objects.filter(slug__isnull=False).values_list('slug', flat=True))
        print(slug_list)
        for partner in slug_less_partners:
            slug = slugify.slugify(partner.name)[:50]
            #necessary because unique constraint on the name field wasn't set from the beginning
            if slug in slug_list:
                slug += '-2'
                #this simple logic should work until 19 partners with the same name
                while slug in slug_list:
                    slug = slug[:-1] + str(int(slug[-1])+1)
            partner.slug = slug
            partner.save()
            slug_list.append(slug)
        print("created {} slugs".format(len(slug_less_partners)))
