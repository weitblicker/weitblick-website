from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import django_google_maps.fields
import localflavor.generic.models
import rules.contrib.models
import sortedm2m.fields
import wbcore.models

class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('wbcore', '0001_initial'),
        ('schedule', '0012_auto_20191025_1852'),
    ]
        
    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('event_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='schedule.Event')),
                ('title_de', models.CharField(max_length=255, null=True, verbose_name='title')),
                ('title_en', models.CharField(max_length=255, null=True, verbose_name='title')),
                ('title_fr', models.CharField(max_length=255, null=True, verbose_name='title')),
                ('title_es', models.CharField(max_length=255, null=True, verbose_name='title')),
                ('description_de', models.TextField(blank=True, null=True, verbose_name='description')),
                ('description_en', models.TextField(blank=True, null=True, verbose_name='description')),
                ('description_fr', models.TextField(blank=True, null=True, verbose_name='description')),
                ('description_es', models.TextField(blank=True, null=True, verbose_name='description')),
                ('slug', models.SlugField(null=True, unique=True)),
                ('teaser', models.TextField(blank=True, max_length=120)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('published', models.DateTimeField(auto_now_add=True, null=True)),
                ('cost', models.CharField(blank=True, default='', max_length=50)),
                ('form', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='form_designer.Form')),
                ('host', models.ManyToManyField(to='wbcore.Host')),
                ('image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='wbcore.Photo')),
                ('location', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='wbcore.Location')),
                ('photos', sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, related_name='events', to='wbcore.Photo', verbose_name='photos')),
                ('projects', models.ManyToManyField(blank=True, to='wbcore.Project')),
            ],
            options={
                'get_latest_by': ['start'],
            },
            bases=(rules.contrib.models.RulesModelMixin, 'schedule.event'),
        ),
    ]
