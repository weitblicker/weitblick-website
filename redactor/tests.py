import unittest
from urlparse import urljoin

from django import forms
from django.conf import settings

from redactor import fields, widgets


class MyForm(forms.Form):
    text = forms.CharField(widget=widgets.RedactorEditor())


class MyAdminForm(forms.Form):
    """ Uses a redactor widget."""
    text = forms.CharField(widget=widgets.AdminRedactorEditor())


class MyOtherAdminForm(forms.Form):
    """ Uses a redactor field."""
    text = fields.RedactorField(widget=widgets.AdminRedactorEditor())


class MySpanishForm(forms.Form):
    """ Uses a redactor widget."""
    text = forms.CharField(widget=widgets.RedactorEditor(
        redactor_css="styles/bodycopy.css",
        redactor_settings={'lang': 'es'}
    ))


class MyOtherSpanishForm(forms.Form):
    """ Uses a redactor field."""
    text = fields.RedactorField(
        redactor_css="styles/bodycopy.css",
        redactor_settings={'lang': 'es'}
    )


class NoJqueryForm(forms.Form):
    """ Uses a redactor field with no no jQuery in media."""
    text = forms.CharField(widget=widgets.RedactorEditor(include_jquery=False))


class RedactorTests(unittest.TestCase):

    def test_field_rendering(self):
        """
        Ensure a widget and a field render the same way.
        """
        form_with_widget = MySpanishForm()
        form_with_field = MyOtherSpanishForm()
        self.assertEqual(
            form_with_widget.as_p(),
            form_with_field.as_p()
        )
        form_with_widget = MyAdminForm()
        form_with_field = MyOtherAdminForm()
        self.assertEqual(
            form_with_widget.as_p(),
            form_with_field.as_p()
        )

    def test_widget_rendering(self):
        """
        Ensure that the form widget renders as expected.
        """
        form = MyForm()
        html = form.as_p()
        js = (
            'Redactor.register({"lang": "en", "load": true, "autoresize": true, '
            '"focus": false, "path": false});'
        )
        el = (
            '<textarea class="redactor_content" cols="40" id="id_text" '
            'name="text" rows="10">'
        )
        self.assertTrue(js in html)
        self.assertTrue(el in html)

        self.assertFalse('django_admin.css' in "".join(form.media.render_css()))

        admin_form = MyAdminForm()
        self.assertTrue('django_admin.css' in "".join(admin_form.media.render_css()))

        spanish_form = MySpanishForm()
        spanish_html = spanish_form.as_p()
        self.assertTrue('"lang": "es"' in spanish_html)
        base_url = settings.STATIC_URL = None and settings.MEDIA_URL or settings.STATIC_URL
        css_url = urljoin(base_url, "styles/bodycopy.css")
        self.assertTrue('"css": "%s"' % css_url in spanish_html)
        self.assertFalse('django_admin.css' in "".join(spanish_form.media.render_css()))

        no_jquery_form = NoJqueryForm()
        jq_scripts = filter(lambda s: "django-redactor/lib/jquery-1.9.0.min.js" in s, no_jquery_form.media.render_js())
        self.assertTrue(len(jq_scripts) == 0)
        yes_jquery_form = MyForm()
        jq_scripts = filter(lambda s: "django-redactor/lib/jquery-1.9.0.min.js" in s, yes_jquery_form.media.render_js())
        self.assertTrue(len(jq_scripts) == 1)
