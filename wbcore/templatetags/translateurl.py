
from django import template
from django.urls import reverse
from django.urls import resolve
from django.utils import translation

register = template.Library()


class TranslatedURL(template.Node):
    def __init__(self, lang_code):
        self.language = template.Variable(lang_code)

    def render(self, context):
        try:
            view = resolve(context['request'].path)
            request_language = translation.get_language()
            translation.activate(self.language.resolve(context))
            url = reverse(view.url_name, args=view.args, kwargs=view.kwargs)
            translation.activate(request_language)
            return url
        except template.VariableDoesNotExist:
            return ''


@register.tag(name='translate_url')
def do_translate_url(parser, token):
    tag, lang_code = token.split_contents()
    return TranslatedURL(lang_code)
