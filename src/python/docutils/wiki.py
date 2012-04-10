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
        self.section_refs = dict()
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
        self.in_literal = False
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
        self.in_definition_list = False
        self.definition_start = None
        self.definition_end = None
        self.definition_term_start = None
        self.definition_term_end = None
        self.in_paragraph = False
        self.footnote_refs = dict()

    def astext(self):
        for idx, item in enumerate(self.body):
            if not isinstance(item, tuple):
                continue
            #
            # We have encountered a tuple which represents
            # a function we have to render to extract text.
            #
            # Deferred functions like this are often used
            # to render links which must wait till we walk
            # the document for link discovery.
            # 
            fn = item[0]
            args = item[1:]
            text = fn(*args)
            if not text:
                text = ''
            self.body[idx] = text
        return ''.join(self.body)
    
    def escape(self, text):
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
        text = self.escape(text)
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
        newline = self.escape('\n')

        if (not isinstance(node.parent, nodes.list_item) and
            not self.in_table):
            self.body.append(newline)
            self.body.append(newline)
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
        if node['ids']:
            assert len(node['ids']) == 1
            self.context.append(node['ids'][0])
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

    def title_anchor(self, title):
        """A method which returns the anchor which will be autogenerated
        for title.
        """
        return title
    
    def visit_title(self, node):
        if self.context:
            refid = self.title_anchor(node.astext())
            self.section_refs[self.context.pop()] = refid
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
        self.in_literal = True
        
    def depart_literal(self, node):
        if self.literal_end:
            self.body.append(self.literal_end)
        self.in_literal = False            

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
        if self.list_level == 0:
            self.list_start = True
        self.list_level += 1
        self.in_definition_list = True
        

    def depart_definition_list(self, node):
        self.list_level -= 1
        self.in_definition_list = False

    def visit_definition_list_item(self, node):
        if not self.list_start:
           self.strip()
           self.body.append('\n')        
        self.list_start = False

    def depart_definition_list_item(self, node):
        pass

    def visit_term(self, node):
        if self.definition_term_start:
            self.body.append(self.definition_term_start)

    def depart_term(self, node):
        if self.definition_term_end:
            self.body.append(self.definition_term_end)
        else:
            self.body.append('\n')            

    def visit_definition(self, node):
        if self.definition_start:
            self.body.append(self.definition_start)

    def depart_definition(self, node):
        if self.definition_end:
            self.body.append(self.definition_end)
        else:
            self.body.append('\n')                    
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
        pass

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
    def create_link(self, id=None, uri=None, name=None, text=None):
        """Must return Markup text for a link to something.
        """
        pass

    def visit_reference(self, node):
        self.context.append((self.create_link,
                            node.get('refid'), node.get('refuri'),
                            node.get('name'), node.astext()))
        
    def depart_reference(self, node):
        self.body.pop()
        self.body.append(self.context.pop())

    def create_anchor(self, id=None, uri=None, name=None, text=None):
        """Must return Markup for an anchor."""
        pass
    
    def visit_target(self, node):
        if node.get('anonymous'):
            return
        self.context.append((self.create_anchor,
                            node.get('refid'), node.get('refuri'),
                            node.get('name'), node.astext()))        
    
    def depart_target(self, node):
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
        self.body.append(self.escape('['))
        refid = '%s%s' % (self.footnote_prefix, node.astext())
        self.footnote_refs[node.astext()] = refid
        self.context.append((self.create_link,
                            refid, node.get('refuri'),
                            node.get('name'), node.astext()))        

    def depart_footnote_reference(self, node):
        self.body.pop()
        self.body.append(self.context.pop())        
        self.body.append(self.escape(']'))

    def visit_label(self, node):
        refid = self.footnote_refs.get(node.astext())
        self.body.append((self.create_anchor,
                          refid, node.get('refuri'),
                          node.get('name'), node.astext()))
        self.body.append(' ')
        self.body.append(self.escape('['))
        
    def depart_label(self, node):
        self.body.append(self.escape(']'))
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
        if not self.body[-1][-1].isspace():
            self.body.append('\n')
            self.body.append('\n')
        if self.strong_start:
            self.body.append(self.strong_start)
        self.body.append(name.title())
        if self.strong_end:
            self.body.append(self.strong_end)
        self.body.append(':')
        self.body.append('\n')
        self.body.append('\n')
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
        # Inline literal's *must* begin and end with a space
        self.literal_start = ' ='
        self.literal_end = '= '
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
        self.section_anchors = list()          # Track section anchors we have seen
        self.footnote_prefix = 'FootNote'
        
    def escape(self, text):
        if self.in_table:
            text = text.replace('\n', ' \\\n')
        if not self.in_literal_block:
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
        return text
    
    def title_prefix(self):
        return '---%s ' % ('+' * self.section_level)

    def title_anchor(self, title):
        count = 0
        prefix = '_'.join(title.strip('()?:').split())
        while True:
            if count:
                anchor = '%s_AN%d' % (prefix, count)
            else:
                anchor = prefix
            if anchor not in self.section_anchors:
                break
            count += 1
        self.section_anchors.append(anchor)
        return anchor
    
    def list_prefix(self, type):
        if self.in_table:
            return '<li>'
        depth = self.list_level
        if self.in_definition_list:
            depth -= 1
        if type == 'bullet':
            return '%s* ' % (' ' * (depth * self._list_indent))
        if type == 'enumerated':
            return '%s1. ' % (' ' * (depth * self._list_indent))

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
    def create_link(self, id=None, uri=None, name=None, text=None):
        if not name:
            name = text
        if id:
            # Sections have special anchors
            if id in self.section_refs:
                id = self.section_refs[id]
            if name:
                return '[[#%s][%s]]' % (id, name)
            else:
                return '[[#%s]]' % id
        if uri:
            if 'mail' in uri:
                return '[[%s][%s]]' % (uri, name)
            elif name:
                return '[[%s][%s]]' % (uri, name)
            else:
                return '[[%s]]' % uri

    def create_anchor(self, id=None, uri=None, name=None, text=None):
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
        self.definition_start = '{quote}'
        self.definition_end = '{quote}'
        self.definition_term_start = None
        self.definition_term_end = None
        self.anchor_start = '[#'
        self.anchor_end = ']'
        self.link_start = None
        self.link_end = None
        self.link_name_start = None
        self.link_name_end = None
        self.footnote_prefix = 'foot-note-'
        
    def escape(self, text):
        text = text.replace('[', '\[')
        text = text.replace(']', '\]')
        text = text.replace('{', '\{')
        text = text.replace('}', '\}')
        if self.in_literal:
            text = text.replace('*', '\*')
            text = text.replace(r'\\*', '\*') # incase we already escaped
        return text
    
    def title_prefix(self):
        return 'h%s. ' % self.section_level

    def list_prefix(self, type):
        depth = self.list_level
        if self.in_definition_list:
            depth -= 1
        if type == 'bullet':
            return '%s ' % ('*' * depth)
        elif type == 'enumerated':
            return '%s ' % ('#' * depth)

    def create_link(self, id=None, uri=None, name=None, text=None):
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

    def create_anchor(self, id=None, uri=None, name=None, text=None):
        if id:
            return '{anchor:%s}' % id
        if uri:
            return '[%s]' % uri
        
    def image(self, uri):
        return '!%s!' % uri
