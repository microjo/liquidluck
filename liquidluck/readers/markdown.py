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

    def _do_auto_links(self, text):
        variables = settings.reader.get('vars') or {}
        for func in variables.get(
            'markdown_transform', [
                'liquidluck.readers.markdown.transform_youtube',
                'liquidluck.readers.markdown.transform_gist',
                'liquidluck.readers.markdown.transform_vimeo',
                'liquidluck.readers.markdown.transform_github',
            ]):
            func = import_object(func)
            text = func(text)

        text = super(LLMarkdown, self)._do_auto_links(text)
        return text

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

    md = LLMarkdown(extras=['code-friendly', 'fenced-code-blocks', 'footnotes',
        'toc', 'wiki-tables'])
    return md.convert(text)


# _XHTML_ESCAPE_RE = re.compile('[&<>"]')
# _XHTML_ESCAPE_DICT = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}


# def escape(value):
#     """Escapes a string so it is valid within XML or XHTML."""
#     if not isinstance(value, (basestring, type(None))):
#         value = value.decode('utf-8')
#     return _XHTML_ESCAPE_RE.sub(
#         lambda match: _XHTML_ESCAPE_DICT[match.group(0)], value)


#: markdown autolink transform

def transform_youtube(text):
    #: youtube.com
    def auto_youtube_link_sub(match):
        link = match.group(0)[1:][:-1]
        title = link.replace('http://','')
        return ('<iframe width="560" height="315" src='
                '"http://www.youtube.com/embed/%(id)s" '
                'frameborder="0" allowfullscreen></iframe>'
                '<span><a rel="nofollow" href="%(link)s">'
                '%(title)s</a></span>'
                ) % {'id': match.group(1), 'link': link, 'title': title}

    auto_youtube_link_re = re.compile(r'<http://www.youtube.com/watch\?v=([a-zA-Z0-9\-\_]+)>', re.I)
    text = auto_youtube_link_re.sub(auto_youtube_link_sub, text)
    auto_youtube_link_re = re.compile(r'<http://youtu.be/([a-zA-Z0-9\-\_]+)>', re.I)
    return auto_youtube_link_re.sub(auto_youtube_link_sub, text)


def transform_gist(text):
    #: gist support
    def auto_gist_link_sub(match):
        link = match.group(1)
        title = link.replace('http://', '').replace('https://', '')
        return ('<script src="%(link)s.js"></script>'
                '<span><a rel="nofollow" href="%(link)s">'
                '%(title)s</a></span>'
                ) % {'link': link, 'title': title}

    auto_gist_link_re = re.compile(r'<(https?://gist.github.com/[\d]+)>', re.I)
    return auto_gist_link_re.sub(auto_gist_link_sub, text)


def transform_vimeo(text):
    #: vimeo.com
    def auto_vimeo_link_sub(match):
        link = match.group(0)[1:][:-1]
        title = link.replace('http://','')
        return ('<iframe width="500" height="281" frameborder="0" '
                'src="http://player.vimeo.com/video/%(id)s" '
                'allowFullScreen></iframe>'
                '<span><a rel="nofollow" href="%(link)s">'
                '%(title)s</a></span>'
                ) % {'id': match.group(1), 'link': link, 'title': title}

    auto_vimeo_link_re = re.compile(r'<http://vimeo.com/([\d]+)>', re.I)
    return auto_vimeo_link_re.sub(auto_vimeo_link_sub, text)


def transform_screenr(text):
    #: screenr.com
    def auto_screenr_link_sub(match):
        link = match.group(0)[1:][:-1]
        title = link.replace('http://','')
        return ('<iframe width="500" height="305" frameborder="0" '
                'src="http://www.screenr.com/embed/%(id)s" '
                'allowFullScreen></iframe>'
                '<span><a rel="nofollow" href="%(link)s">'
                '%(title)s</a></span>'
                ) % {'id': match.group(1), 'link': link, 'title': title}

    auto_screenr_link_re = re.compile(r'<http://www.screenr.com/([a-zA-Z0-9]+)>', re.I)
    return auto_screenr_link_re.sub(auto_screenr_link_sub, text)


def transform_github(text):
    #: github
    def auto_github_link_sub(match):
        link = 'http://github.com/%s/%s/commit/%s' % (match.group(1), match.group(2), match.group(3))
        title = '%s/%s@%s' % (match.group(1), match.group(2), match.group(3)[:7])
        return ('<a rel="nofollow" href="%(link)s">'
                '%(title)s</a>'
                ) % {'link': link, 'title': title}

    auto_github_link_re = re.compile(r'([a-zA-Z0-9]+)/([a-zA-Z0-9_\-]+)@([a-fA-F0-9]{40})')
    return auto_github_link_re.sub(auto_github_link_sub, text)
