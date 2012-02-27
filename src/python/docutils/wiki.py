# Copyright (c) 2011-2012, Joshua Graff
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice, this
#        list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above copyright notice,
#        this list of conditions and the following disclaimer in the documentation
#        and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os

from docutils import nodes, writers, languages


class Writer(writers.Writer):

    supported = ('twiki', 'confluence')

    output = None

    settings_spec = (
        'Wiki-Specific Options',
        None,
        (
        ('Specify Wiki markup language (default \'%s\'). '
         'Valid options: %s' % ('twiki', ', '.join(supported)),
         ['--wiki'], {'default': 'twiki',
                      'choices': supported}),
        ))
    def __init__(self):
        writers.Writer.__init__(self)

    def translate(self):
        if self.document.settings.wiki == 'twiki':
            visitor = TWikiTranslator(self.document)
        elif self.document.settings.wiki == 'confluence':
            visitor = ConfluenceTranslator(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()


class WikiTranslator(nodes.NodeVisitor):
    
    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.settings = settings = document.settings
        lcode = settings.language_code
        self.language = languages.get_language(lcode, document.reporter)
        self.body = list()
        self.context = list()
        self.section_level = 1
        self.list_level = 0
        self.list_type = list()
        self.emphasis_start = None
        self.emphasis_end = None
        self.strong_start = None
        self.strong_end = None
        self.literal_start = None
        self.literal_end = None
        self.title_reference_start = None
        self.title_reference_end = None
        self.in_literal_block = False
        self.literal_block_start = None
        self.literal_block_end = None
        self.literal_block_indent = 2
        self.in_table = False
        self.in_table_header = False
        self.table_header_width = 0
        self.table_entry_width = 0
        self.table_header_sep = None
        self.table_entry_sep = None
        self.options = list()
        self.description = None
        self.toc = None
        self.block_quote_start = None
        self.block_quote_end = None
        self.definition_term_start = None
        self.definition_term_end = None
        self.in_paragraph = False

    def astext(self):
        return ''.join(self.body)

    def escape(self, text, in_table, in_literal_block):
        return text    

    def strip(self):
        """Remove all whitespace at the end of self.body."""
        while self.body and not self.body[-1].strip():
            self.body.pop()
        self.body[-1] = self.body[-1].rstrip()

    def visit_document(self, node):
        pass

    def depart_document(self, node):
        self.body.append('\n')

    def visit_Text(self, node):
        text = node.astext()
        if (self.in_paragraph or self.list_level) and not self.in_literal_block:
            text = text.replace('\n', ' ')
        text = self.escape(text, self.in_table, self.in_literal_block)
        if self.in_literal_block:
            # Add indent space to all literal blocks. Take into account
            # the depth of a list.
            space = ' ' * (self.literal_block_indent * (self.list_level * 3))
            text = ''.join(['%s%s' % (space, line)
                            for line in text.splitlines(True)])
        self.body.append(text)
    
    def depart_Text(self, node):
        pass

    def visit_comment(self, node):
        raise nodes.SkipNode

    def depart_comment(self):
        pass
    
    def visit_paragraph(self, node):
        self.in_paragraph = True
    
    def depart_paragraph(self, node):
        # newline may be escaped within a table
        newline = self.escape('\n', self.in_table, self.in_literal_block)
        self.body.append(newline)
        self.body.append(newline)
#         if (not isinstance(node.parent, nodes.list_item) and
#             not self.in_table):
#             self.body.append(newline)
        self.in_paragraph = False            

    ##
    # Table of contents
    #
    def visit_topic(self, node):
        self.body.append(self.toc)
        self.body.append('\n')
        self.section_level -= 1
        raise nodes.SkipNode

    def depart_topic(self, node):
        pass
    #
    # End table of contents
    ##
        
    ##
    # Title/Section
    #
    def visit_section(self, node):
        self.section_level += 1
        self.body.append('\n')

    def depart_section(self, node):
        self.section_level -= 1
        
    def title_prefix(self):
        """A method which returns a title prefix based on self.section_level.

        self.section_level will be the current title depth from 1 - N where
        1 is the highest thus top most title.
        """
        pass
    
    def visit_title(self, node):
        self.body.append(self.title_prefix())

    def depart_title(self, node):
        self.body.append('\n\n')
    #
    #
    ##

    ###
    # Paragraphs emphasis
    #
    def visit_literal(self, node):
        if self.literal_start:
            self.body.append(self.literal_start)
        
    def depart_literal(self, node):
        if self.literal_end:
            self.body.append(self.literal_end)

    def visit_emphasis(self, node):
        if self.emphasis_start:
            self.body.append(self.emphasis_start)

    def depart_emphasis(self, node):
        if self.emphasis_end:
            self.body.append(self.emphasis_end)

    def visit_strong(self, node):
        if self.strong_start:
            self.body.append(self.strong_start)

    def depart_strong(self, node):
        if self.strong_end:
            self.body.append(self.strong_end)

    def visit_title_reference(self, node):
        if self.title_reference_start:
            self.body.append(self.title_reference_start)

    def depart_title_reference(self, node):
        if self.title_reference_end:
            self.body.append(self.title_reference_end)
    #
    #
    ##

    ###
    # Blocks
    # NOTE: For block quotes we only quote raw text, and never
    #       anything that would result in markup
    #
    def visit_block_quote(self, node):
        for child in node.children:
            if not isinstance(child, nodes.paragraph):
                return

        if self.block_quote_start:
            self.body.append(self.block_quote_start)
            self.body.append('\n')
            
    def depart_block_quote(self, node):
        for child in node.children:
            if not isinstance(child, nodes.paragraph):
                return
        if self.block_quote_end:
            if not self.body[-1].endswith('\n'):
                self.body.append('\n')
            self.body.append(self.block_quote_end)
            self.body.append('\n')
            
    def visit_literal_block(self, node):
        self.in_literal_block = True
        if self.literal_block_start:
            self.body.append(self.literal_block_start)
            self.body.append('\n')

    def depart_literal_block(self, node):
        self.in_literal_block = False
        if self.literal_block_end:
            if not self.body[-1].endswith('\n'):
                self.body.append('\n')
            self.body.append(self.literal_block_end)
            self.body.append('\n')
    #
    #
    ##

    ###
    # List items
    #
    def list_prefix(self, type):
        """A method which returns a list prefix based on the list's type
        and self.list_level.

        Where: 
          type: will be 'bullet', 'definition', 'enumerated', 'field',
                or 'option'
          self.list_level is 1 - N
        """
        pass

    def visit_list_item(self, node):
        # No extra whitespace between list items
        if not self.list_start:
           self.strip()
           self.body.append('\n')
        self.body.append(self.list_prefix(self.list_type[-1]))
        self.list_start = False

    def depart_list_item(self, node):
        pass
    
    def visit_bullet_list(self, node):
        if self.list_level == 0:
            self.list_start = True
        self.list_level += 1
        self.list_type.append('bullet')

    def depart_bullet_list(self, node):
        self.list_level -= 1
        self.list_type.pop()
        
    def visit_enumerated_list(self, node):
        if self.list_level == 0:
            self.list_start = True
        self.list_level += 1
        self.list_type.append('enumerated')

    def depart_enumerated_list(self, node):
        self.list_level -= 1
        self.list_type.pop()
    #
    #
    ###

    ###
    # Field lists
    #
    def visit_field(self, node):
        pass

    def depart_field(self, node):
        pass

    def visit_field_name(self, node):
        self.body.append(self.strong_start)

    def depart_field_name(self, node):
        self.body.append(self.strong_end)
        self.body.append(': ')

    def visit_field_body(self, node):
        pass

    def depart_field_body(self, node):
        pass

    def visit_field_list(self, node):
        pass

    def depart_field_list(self, node):
        pass
    #
    #
    ###

    ###
    # Definition lists
    #
    def visit_definition_list(self, node):
        pass

    def depart_definition_list(self, node):
        pass

    def visit_definition_list_item(self, node):
        pass

    def depart_definition_list_item(self, node):
        pass

    def visit_term(self, node):
        if self.definition_term_start:
            self.body.append(self.definition_term_start)

    def depart_term(self, node):
        if self.definition_term_end:
            self.body.append(self.definition_term_end)

    def visit_definition(self, node):
        pass

    def depart_definition(self, node):
        pass
    #
    #
    ###
    
    ###
    # Table visitors
    #
    def visit_table(self, node):
        self.in_table = True
        self.table_header_width = 0

    def depart_table(self, node):
        self.in_table = False

    def visit_entry(self, node):
        if self.in_table_header:
            self.body.append(self.table_header_sep)
            self.table_header_width += 1
        else:
            self.body.append(self.table_entry_sep)
            self.table_entry_width += 1

    def depart_entry(self, node):
        # Remove paragraph newline
        self.body.pop()
    
    def visit_row(self, node):
        pass

    def depart_row(self, node):
        # Add end of table markup
        if self.in_table_header:
            self.body.append(self.table_header_sep)
        else:
            while self.table_entry_width < self.table_header_width:
                self.body.append(self.table_entry_sep)
                self.table_entry_width += 1
            self.body.append(self.table_entry_sep)                
                
        self.body.append('\n')
        self.table_entry_width = 0
        
    def visit_colspec(self, node):
        pass

    def depart_colspec(self, node):
        pass

    def visit_tgroup(self, node):
        pass
    
    def depart_tgroup(self, node):
        pass

    def visit_thead(self, node):
        self.in_table_header = True
    
    def depart_thead(self, node):
        self.in_table_header = False

    def visit_tbody(self, node):
        pass
    
    def depart_tbody(self, node):
        pass
    #
    # End Table
    ###

    ##
    # Options
    #
    def visit_option(self, node):
        pass
    
    def depart_option(self, node):
        self.body.append(', ')

    def visit_option_argument(self, node):
        self.body.append('=')
    
    def depart_option_argument(self, node):
        pass

    def visit_option_string(self, node):
        pass
    
    def depart_option_string(self, node):
        pass

    def visit_option_group(self, node):
        self.body.append(self.literal_start)
    
    def depart_option_group(self, node):
        # XXX Remove extra comma
        if self.body[-1] == ', ':
            self.body.pop()
        self.body.append(self.literal_end)
        self.body.append('\n\n')
    
    def visit_option_list(self, node):
        pass
    
    def depart_option_list(self, node):
        pass
    
    def visit_option_list_item(self, node):
        self.options = list()
        self.body.append('\n')
    
    def depart_option_list_item(self, node):
        pass
    
    def visit_description(self, node):
        pass
    
    def depart_description(self, node):
        pass
    #
    #
    ###
               
    ###
    # Links
    #
    def create_link(self, id, uri, name, text):
        """Must return Markup text for a link to something.
        """
        pass
    
    def visit_reference(self, node):
        text = self.create_link(node.get('refid'), node.get('refuri'),
                                node.get('name'), node.astext())
        if text:
            self.context.append(text)

    def depart_reference(self, node):
        if self.context:
            self.body.pop()
            self.body.extend(self.context)
            self.context = list()

    def create_anchor(self, id, uri, name, text):
        """Must return Markup for an anchor."""
        pass
    
    def visit_target(self, node):
        if node.get('anonymous'):
            return
        import pdb; pdb.set_trace()
        text = self.create_anchor(node.get('refid'), node.get('refuri'),
                                  node.get('name'), node.astext())
        if text:
            self.context.append(text)
            self.context.append('\n')
    
    def depart_target(self, node):
        import pdb; pdb.set_trace()
        if self.context:
            self.body.pop()
            self.body.extend(self.context)
            self.context = list()
    #
    #
    ###

    ###
    # Start Image
    #
    def visit_image(self, node):
        # XXX add more support for scaling
        if 'uri' in node:
            self.body.append(self.image(node['uri']))
            self.body.append('\n\n')
        raise nodes.SkipNode            
                
    def depart_image(self, node):
        pass

    #
    # End Image
    ###

    ###
    # Begin footnote
    #
    def visit_footnote(self, node):
        pass

    def depart_footnote(self, node):
        pass

    def visit_footnote_reference(self, node):
        pass

    def depart_footnote_reference(self, node):
        pass

    def visit_label(self, node):
        pass

    def depart_label(self, node):
        pass
    #
    # End footnote
    ###

    ###
    # Start Docinfo
    #
    def visit_docinfo(self, node):
        pass
    
    def depart_docinfo(self, node):
        pass

    def visit_version(self, node):
        self.body.append(self.strong_start)
        self.body.append('Version')
        self.body.append(self.strong_end)
        self.body.append(': ')
    
    def depart_version(self, node):
        self.body.append('\n\n')
    
    def visit_author(self, node):
        self.body.append(self.strong_start)
        self.body.append('Author')
        self.body.append(self.strong_end)
        self.body.append(': ')
    
    def depart_author(self, node):
        self.body.append('\n\n')
    #
    # End Docinfo
    ###

    ###
    # Start Admonition
    #
    def visit_attention(self, node):
        self.admonition('attention')

    def depart_attention(self, node):
        pass

    def visit_caution(self, node):
        self.admonition('caution')

    def depart_caution(self, node):
        pass

    def visit_danger(self, node):
        self.admonition('danger')

    def depart_danger(self, node):
        pass

    def visit_error(self, node):
        self.admonition('error')

    def depart_error(self, node):
        pass

    def visit_hint(self, node):
        self.admonition('hint')

    def depart_hint(self, node):
        pass

    def visit_important(self, node):
        self.admonition('important')

    def depart_important(self, node):
        pass

    def visit_note(self, node):
        self.admonition('note')

    def depart_note(self, node):
        pass

    def visit_tip(self, node):
        self.admonition('tip')

    def depart_tip(self, node):
        pass

    def visit_warning(self, node):
        self.admonition('warning')

    def depart_warning(self, node):
        pass

    def visit_admonition(self, node):
        pass

    def depart_admonition(self, node):
        pass

    def admonition(self, name):
        if self.strong_start:
            self.body.append(self.strong_start)
        self.body.append(name.title())
        if self.strong_end:
            self.body.append(self.strong_end)
        self.body.append(':')
        self.body.append('\n\n')
    #
    # End Admonition
    ###
    
class TWikiTranslator(WikiTranslator):

    def __init__(self, document):
        WikiTranslator.__init__(self, document)
        self._list_indent = 3
        self.emphasis_start = '_'
        self.emphasis_end = '_'
        self.strong_start = '*'
        self.strong_end = '*'
        self.literal_start = '='
        self.literal_end = '='
        self.title_reference_start = '_'
        self.title_reference_end = '_'
        self.literal_block_start = '<verbatim>'
        self.literal_block_end = '</verbatim>'
        self.table_header_sep = '|'
        self.table_entry_sep = '|'
        self.toc = '%TOC%'
        self.block_quote_start = '<literal><blockquote>'
        self.block_quote_end = '</blockquote></literal>'
        self.definition_term_start = '   $ '
        self.definition_term_end = ': '
        
    def escape(self, text, in_table, in_literal_block):
        if in_table:
            text = text.replace('\n', ' \\\n')
        if not in_literal_block:
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
        return text
    
    def title_prefix(self):
        return '---%s ' % ('+' * self.section_level)

    def list_prefix(self, type):
        if self.in_table:
            return '<li>'
        if type == 'bullet':
            return '%s* ' % (' ' * (self.list_level * self._list_indent))
        if type == 'enumerated':
            return '%s1. ' % (' ' * (self.list_level * self._list_indent))

    ###
    # TWiki doesn't support lists in using Wiki syntax within
    # a table, so the logic below moves to HTML when in side
    # a table.
    #
    def depart_list_item(self, node):
        WikiTranslator.depart_list_item(self, node)
        if self.in_table:
            self.body.pop()             # remove endline
            self.body.append('</li>')

    def visit_bullet_list(self, node):
        WikiTranslator.visit_bullet_list(self, node)
        if self.in_table:
            self.body.append('<ul>')

    def depart_bullet_list(self, node):
        WikiTranslator.depart_bullet_list(self, node)
        if self.in_table:
            self.body.append('</ul>')
            # Null gets popped off the stack on table entry departure
            self.body.append('')        
        
    def visit_enumerated_list(self, node):
        WikiTranslator.visit_enumerated_list(self, node)
        if self.in_table:
            self.body.append('<ol>')
        
    def depart_enumerated_list(self, node):
        WikiTranslator.depart_enumerated_list(self, node)
        if self.in_table:
            self.body.append('</ol>')
            # Null gets popped off the stack on table entry departure
            self.body.append('')        
    #
    # End section
    ###

    ###
    # TWiki requires some extra strong emphasis for table headers
    #
    def visit_entry(self, node):
        WikiTranslator.visit_entry(self, node)
        if self.in_table_header:
            self.body.append(self.strong_start)
        
    def depart_entry(self, node):
        WikiTranslator.depart_entry(self, node)
        if self.in_table_header:
            self.body.append(self.strong_end)
    #
    # End section
    ###

    ###
    # Links
    #
    def create_link(self, id, uri, name, text):
        if not name:
            name = text
        if id:
            if name:
                return '[[%s][%s]]' % (id, name)
            else:
                return '[[#%s]]' % id
        if uri:
            if 'mail' in uri:
                return '[[%s][%s]]' % (uri, name)
            elif name:
                return '[[%s][%s]]' % (uri, name)
            else:
                return '[[%s]]' % uri

    def create_anchor(self, id, uri, name, text):
        if id:
            return '#%s' % id
        if uri:
            return '[[%s]]' % uri
    #
    # End Links
    ###

    def image(self, uri):
        return os.path.normpath('%ATTACHURL%/' + uri)
    
class ConfluenceTranslator(WikiTranslator):

    def __init__(self, document):
        WikiTranslator.__init__(self, document)
        self.emphasis_start = '_'
        self.emphasis_end = '_'
        self.strong_start = '*'
        self.strong_end = '*'
        self.literal_start = '{{'
        self.literal_end = '}}'
        self.title_reference_start = '_'
        self.title_reference_end = '_'
        self.literal_block_start = '{noformat}'
        self.literal_block_end = '{noformat}'
        self.table_header_sep = '||'
        self.table_entry_sep = '|'
        self.toc = '{toc}'
        self.block_quote_start = '{quote}'
        self.block_quote_end = '{quote}'
        self.definition_term_start = '*'
        self.definition_term_end = '* '
        self.anchor_start = '[#'
        self.anchor_end = ']'
        self.link_start = None
        self.link_end = None
        self.link_name_start = None
        self.link_name_end = None        
        
    def escape(self, text, in_table, in_literal_block):
        text = text.replace('[', '\[')
        text = text.replace(']', '\]')
        text = text.replace('{', '\{')
        text = text.replace('}', '\}')
        return text
    
    def title_prefix(self):
        return 'h%s. ' % self.section_level

    def list_prefix(self, type):
        if type == 'bullet':
            return '%s ' % ('*' * self.list_level)
        elif type == 'enumerated':
            return '%s ' % ('#' * self.list_level)

    def create_link(self, id, uri, name, text):
        if not name:
            name = text
        if id:
            if name:
                return '[%s|#%s]' % (name, id)
            else:
                return '[#%s]' % id
        if uri:
            if 'mail' in uri:
                pass
            elif name:
                return '[%s|%s]' % (name, uri)
            else:
                return '[%s]' % uri        
        if id:
            if text:
                return '[%s|#%s]' % (text, id)
            else:
                return '[#%s]' % id 

    def create_anchor(self, id, uri, name, text):
        if id:
            return '{anchor:%s}' % id
        if uri:
            return '[%s]' % uri
        
    def image(self, uri):
        return '!%s!' % uri
