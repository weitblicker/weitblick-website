from location_field.widgets import LocationWidget
import six
import json

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

class CustomLocationWidget(LocationWidget):
    """
    As the model field is neither a char nor a geolocation Point object but a GTPoint defined by the package
    django_google_maps, we need to override the render function.
    """

    def render(self, name, value, attrs=None, renderer=None):
        if value is not None:
            try:
                if isinstance(value, six.string_types):
                    lat, lng = value.split(',')
                else: # overriden definitions
                    lng = value.lon     #lng = value.x
                    lat = value.lat     #lat = value.y

                value = '%s,%s' % (
                    float(lat),
                    float(lng),
                )
            except ValueError:
                value = ''
        else:
            value = ''

        if '-' not in name:
            prefix = ''
        else:
            prefix = name[:name.rindex('-') + 1]

        self.options['field_options']['prefix'] = prefix

        attrs = attrs or {}
        attrs['data-location-field-options'] = json.dumps(self.options)

        text_input = super(LocationWidget, self).render(name, value, attrs)
        return render_to_string('location_field/map_widget.html', {
            'field_name': name,
            'field_input': mark_safe(text_input)
        })
