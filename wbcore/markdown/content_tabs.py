from markdown import util
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagPattern, ImageInlineProcessor, LinkInlineProcessor, IMAGE_LINK_RE
import re


class ContentTabProcessor(BlockProcessor):

    RE = re.compile(r'# \[(.*?)\]\(#tab/([a-zA-Z0-9\-]+)(?:/([a-zA-Z0-9\-]+)?)?\)')
    RE_BREAK = re.compile(r'(.*?)(---)(.*?)')

    def test(self, parent, block):
        se = self.RE.search(block)
        #print("re:", se)
        return bool(se)

    def run(self, parent, blocks):
        collection = []

        container = util.etree.Element("ui container")
        parent.append(container)
        menu = util.etree.Element("div")
        menu.set("class", "ui top attached tabular menu")
        container.append(menu)
        container.tail('<script type="text/javascript">$(".menu .item").tab();</script>')

        first = None

        while blocks:
            block = blocks.pop(0)
            m = self.RE.search(block)
            print(m, block)
            if m:
                title = m.groups()[0]
                id = m.groups()[1]
                block = self.RE.sub("", block)
                #print("Block id:", id, "title:", title, "content:", block)
                button = util.etree.Element("a")
                button.set("class", "item")
                button.set("data-tab", id)
                button.text = title
                menu.append(button)

                content_div = util.etree.Element("div")
                content_div.set("class", "ui bottom attached tab segment")
                content_div.set("data-tab", id)
                container.append(content_div)

                if not first:
                    first = True
                    button.set("class", button.get("class") + " active")
                    content_div.set("class", content_div.get("class") + " active")

                b = self.RE_BREAK.search(block)
                if b:
                    print("BB", b)
                    block = b.groups()[0]
                    self.parser.parseChunk(content_div, block)
                    next_block = b.groups()[2]
                    self.parser.parseChunk(parent, next_block)
                    break
                else:
                    self.parser.parseChunk(content_div, block)
            else:
                break

class MyExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.parser.blockprocessors.register(ContentTabProcessor(md.parser), 'content_tabs', 200)


def makeExtension(**kwargs):  # pragma: no cover
    return MyExtension(**kwargs)
