# -*- coding: utf-8 -*-
'''
Blog content file parser.

Syntax::

    # Title

    - date: 2011-09-01
    - category: life
    - tags: tag1, tag2

    -----------------

    Your content here. And it supports code highlight.

    ```python

    def hello():
        return 'Hello World'

    ```


:copyright: (c) 2012 by Hsiaoming Yang (aka lepture)
:license: BSD
'''


import re
import logging
#import misaka as m
import markdown2

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from liquidluck.readers.base import BaseReader
from liquidluck.options import settings
from liquidluck.utils import to_unicode, cjk_nowrap, import_object


class MarkdownReader(BaseReader):
    SUPPORT_TYPE = ['md', 'mkd', 'markdown']

    def render(self):
        f = open(self.filepath)
        logging.debug('read ' + self.relative_filepath)

        header = ''
        body = ''
        recording = True
        for line in f:
            if recording and line.startswith('---'):
                recording = False
            elif recording:
                header += line
            else:
                body += line

        f.close()
        body = to_unicode(body)
        meta = self._parse_meta(header, body)
        content = self._parse_content(body)
        meta['toc'] = content.toc_html
        return self.post_class(self.filepath, content, meta=meta)

    def _parse_content(self, body):
        return markdown(body)

    def _parse_meta(self, header, body):
        header = markdown2.markdown(to_unicode(header))
        titles = re.findall(r'<h1>(.*)</h1>', header)
        if not titles:
            logging.error('There is no title')
            title = None
        else:
            title = titles[0]

        meta = {'title': title}
        items = re.findall(r'<li>(.*?)</li>', header, re.S)
        for item in items:
            index = item.find(':')
            key = item[:index].rstrip()
            value = item[index + 1:].lstrip()
            meta[key] = value

        #: keep body in meta data as source text
        meta['source_text'] = body
        # _toc = m.Markdown(m.HtmlTocRenderer(), 0)
        # meta['toc'] = _toc.render(body)
        return meta


# class LiquidRender(m.HtmlRenderer, m.SmartyPants):
#     def paragraph(self, text):
#         #text = cjk_nowrap(text)
#         #return '<p>%s</p>\n' % text
#         return text

#     def block_code(self, text, lang):
#         if not lang or lang == '+' or lang == '-':
#             return '\n<pre><code>%s</code></pre>\n' % escape(text.strip())

#         hide = lang.endswith('-')
#         inject = lang.endswith('+') or lang.endswith('-')
#         if inject:
#             lang = lang[:-1]
#         inject = inject and lang in ('javascript', 'js', 'css', 'html')

#         html = ''
#         if inject:
#             if lang == 'javascript' or lang == 'js':
#                 tpl = '\n<script>\n%s</script>\n'
#             elif lang == 'css':
#                 tpl = '\n<style>\n%s</style>\n'
#             else:
#                 tpl = '\n<div class="insert-code">%s</div>\n'

#             html = tpl % text

#         if hide and inject:
#             return html

#         variables = settings.reader.get('vars') or {}
#         lexer = get_lexer_by_name(lang, stripall=True)
#         formatter = HtmlFormatter(
#             noclasses=variables.get('highlight_inline', False),
#             linenos=variables.get('highlight_linenos', False),
#         )
#         html += highlight(text, lexer, formatter)
#         return html

#     def autolink(self, link, is_email):
#         if is_email:
#             return '<a href="mailto:%(link)s">%(link)s</a>' % {'link': link}

#         variables = settings.reader.get('vars') or {}
#         for func in variables.get(
#             'markdown_transform', [
#                 'liquidluck.readers.markdown.transform_youtube',
#                 'liquidluck.readers.markdown.transform_gist',
#                 'liquidluck.readers.markdown.transform_vimeo',
#             ]):
#             func = import_object(func)
#             value = func(link)
#             if value:
#                 return value
#         title = link.replace('http://', '').replace('https://', '')
#         return '<a href="%s">%s</a>' % (link, title)


# #: compatible
# JuneRender = LiquidRender


class LLMarkdown(markdown2.Markdown):

    def header_no(self, n):
        # exclude h1 header
        if n == 1:
            return ''

        n = n - 1
        if n > len(self._headers):
            self._headers.append(1)
        elif n == len(self._headers):
            self._headers[-1] += 1
        else:
            # Example: n == 1, _headers = [1,3,2]  =>  _headers = [2]
            del self._headers[n:]
            self._headers[-1] += 1
        return '.'.join(map(str, self._headers))

    def header_id_from_text(self, text, prefix, n):
        header_id = self.header_no(n)
        if prefix and isinstance(prefix, base_string_type):
            header_id = prefix + '-' + header_id
        header_id_text = markdown2._slugify(text)
        if header_id_text:
            header_id = '%s-%s' % (header_id, header_id_text)
        return header_id

    def _toc_add_entry(self, level, id, name):
        if self._toc is None:
            self._toc = []

        variables = settings.reader.get('vars') or {}
        toc_auto_number = variables.get('markdown_toc_auto_number')
        if isinstance(toc_auto_number, bool) and toc_auto_number:
            # get header_no from header_id
            prefix = self.extras["header-ids"]
            if prefix and isinstance(prefix, base_string_type):
                header_no = id.replace(prefix + '-', '')
            else:
                header_no = id
            header_no = header_no.split('-')[0] + ' '
        else:
            header_no = ''

        self._toc.append((level, id, header_no + self._unescape_special_chars(name)))

    def reset(self):
        super(LLMarkdown, self).reset()
        self._headers = [] # stack of current count for that hN header


def markdown(text):
    text = to_unicode(text)
    regex = re.compile(r'^````(\w+)', re.M)
    text = regex.sub(r'````\1+', text)
    regex = re.compile(r'^`````(\w+)', re.M)
    text = regex.sub(r'`````\1-', text)

    # render = LiquidRender(flags=m.HTML_USE_XHTML | m.HTML_TOC)
    # md = m.Markdown(
    #     render,
    #     extensions=(
    #         m.EXT_FENCED_CODE | m.EXT_AUTOLINK | m.EXT_TABLES |
    #         m.EXT_FOOTNOTES | m.EXT_STRIKETHROUGH
    #     ),
    # )
    # return md.render(text)

    # autolink github
    link_patterns = [
        (re.compile(r'([a-zA-Z0-9]+)/([a-zA-Z0-9_\-]+)@([a-fA-F0-9]{40})'), r"http://github.com/\1/\2/commit/\3")
        ]

    md = LLMarkdown(extras=['code-friendly', 'fenced-code-blocks', 'footnotes', 'link-patterns',
        'smarty-pants', 'toc', 'wiki-tables'],
        link_patterns = link_patterns)
    return md.convert(text)


# _XHTML_ESCAPE_RE = re.compile('[&<>"]')
# _XHTML_ESCAPE_DICT = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}


# def escape(value):
#     """Escapes a string so it is valid within XML or XHTML."""
#     if not isinstance(value, (basestring, type(None))):
#         value = value.decode('utf-8')
#     return _XHTML_ESCAPE_RE.sub(
#         lambda match: _XHTML_ESCAPE_DICT[match.group(0)], value)


# #: markdown autolink transform

# def transform_youtube(link):
#     #: youtube.com
#     title = link.replace('http://', '')
#     pattern = r'http://www.youtube.com/watch\?v=([a-zA-Z0-9\-\_]+)'
#     match = re.match(pattern, link)
#     if not match:
#         pattern = r'http://youtu.be/([a-zA-Z0-9\-\_]+)'
#         match = re.match(pattern, link)
#     if match:
#         value = ('<iframe width="560" height="315" src='
#                  '"http://www.youtube.com/embed/%(id)s" '
#                  'frameborder="0" allowfullscreen></iframe>'
#                  '<div><a rel="nofollow" href="%(link)s">'
#                  '%(title)s</a></div>'
#                 ) % {'id': match.group(1), 'link': link, 'title': title}
#         return value
#     return None


# def transform_gist(link):
#     #: gist support
#     title = link.replace('http://', '').replace('https://', '')
#     pattern = r'(https?://gist.github.com/[\d]+)'
#     match = re.match(pattern, link)
#     if match:
#         value = ('<script src="%(link)s.js"></script>'
#                  '<div><a rel="nofollow" href="%(link)s">'
#                  '%(title)s</a></div>'
#                 ) % {'link': match.group(1), 'title': title}
#         return value
#     return None


# def transform_vimeo(link):
#     #: vimeo.com
#     title = link.replace('http://', '')
#     pattern = r'http://vimeo.com/([\d]+)'
#     match = re.match(pattern, link)
#     if match:
#         value = ('<iframe width="500" height="281" frameborder="0" '
#                  'src="http://player.vimeo.com/video/%(id)s" '
#                  'allowFullScreen></iframe>'
#                  '<div><a rel="nofollow" href="%(link)s">'
#                  '%(title)s</a></div>'
#                 ) % {'id': match.group(1), 'link': link, 'title': title}
#         return value
#     return None


# def transform_screenr(link):
#     title = link.replace('http://', '')
#     pattern = r'http://www.screenr.com/([a-zA-Z0-9]+)'
#     match = re.match(pattern, link)
#     if match:
#         value = ('<iframe width="500" height="305" frameborder="0" '
#                  'src="http://www.screenr.com/embed/%(id)s" '
#                  'allowFullScreen></iframe>'
#                  '<div><a rel="nofollow" href="%(link)s">'
#                  '%(title)s</a></div>'
#                 ) % {'id': match.group(1), 'link': link, 'title': title}
#         return value
#     return None
