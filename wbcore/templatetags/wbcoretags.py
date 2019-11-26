from django import template
from django.template import loader
from django.utils.safestring import mark_safe
from martor.utils import markdownify
import re
register = template.Library()

re_img_tag = re.compile(r'(?P<img_tag><img.*?>)')
re_attr = re.compile(r'([a-z]+)? *([a-z-]+)="([^"]+)')

img_template = template.loader.get_template('wbcore/content_image.html')


def img_match(match):
    gd = match.groupdict()
    img_tag = gd['img_tag'] if 'img_tag' in gd else ""
    img = {}

    for result in re_attr.findall(img_tag):
        img[result[1]] = result[2]

    src = img['src'] if 'src' in img else None
    if not src:
        return ""

    context = {
        'size': 'medium',
        'side': 'left',
        'src': src,
        'title': img['title'] if 'title' in img else None,
        'alt': img['alt'] if 'alt' in img else None,
    }
    return img_template.render(context)


def insert_ui_elems(field_name):
    #html = re_img_tag.sub(img_match, field_name)
    #html += '<div class="ui main center aligned text container clearing segment"></div>'
    #html += '<div style="clear:both;"></div>'
    return field_name
    #return html


@register.filter
def safe_markdown(field_name):
    """
    Safe the markdown text as html ouput.

    Usage:
        {% load martortags %}
        {{ field_name|safe_markdown }}

    Example:
        {{ post.description|safe_markdown }}
    """
    return mark_safe(insert_ui_elems(markdownify(field_name)))
