from markdown import util
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagPattern, ImageInlineProcessor, LinkInlineProcessor, IMAGE_LINK_RE
from markdown.treeprocessors import Treeprocessor


class ImageInlineProcessor(LinkInlineProcessor):
    """ Return a img element from the given match. """

    def handleMatch(self, m, data):
        text, index, handled = self.getText(data, m.end(0))
        if not handled:
            return None, None, None

        src, title, index, handled = self.getLink(data, index)
        if not handled:
            return None, None, None

        sizes = ['mini', 'tiny', 'small', 'medium', 'large', 'big', 'huge']
        size = "medium"

        for s in sizes:
            if text.endswith(s):
                text = text.replace(s, "")
                size = s
                break

        side = ""
        ui_class = "ui rounded fluid image"
        if text.endswith("<>"):
            ui_class = "ui rounded centered %s image" % (size,)
            side = "centered"
        elif text.endswith("<"):
            ui_class = "ui rounded left floated %s image" % (size, )
            side = "left floated"
        elif text.endswith(">"):
            side = "right floated"
            ui_class = "ui rounded right floated %s image" % (size, )

        # the outer div object for ui
        div = util.etree.Element("div")
        div.set("class", ui_class)

        # img tag
        img = util.etree.SubElement(div, "img")
        img.set("src", src)
        if side == 'centered':
            img.set("class", "ui centered image")
        if title is not None:
            img.set("title", title)

        img.set('alt', self.unescape(text))

        # if title available show caption div
        if title:
            caption = util.etree.SubElement(div, "div")
            caption.set("class", "ui bottom attached label")
            caption.text = title

        return div, m.start(0), index


class ImageClearTreeprocessor(Treeprocessor):

    def findImgDiv(self, elem):
        for index in range(0, len(elem)):
            class_attr = elem[index].get('class')
            if class_attr and "image" in class_attr and "ui" in class_attr:
                return index
            i = self.findImgDiv(elem[index])
            if i is not None:
                clear = util.etree.Element("div")
                clear.set("style", "clear:both;")
                elem[index].insert(i, clear)

        return None

    def run(self, root):
        """ Crawl the footnote div and add missing duplicate footnotes. """
        self.findImgDiv(root)
        return None
                    #if div.get("class").contains("image"):
                    #    print(index)


class MyExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.register(ImageInlineProcessor(IMAGE_LINK_RE, md), 'image_link', 150)
        md.treeprocessors.register(ImageClearTreeprocessor(), 'image_clear', 20)


def makeExtension(**kwargs):  # pragma: no cover
    return MyExtension(**kwargs)
