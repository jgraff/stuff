#!/usr/bin/env python
# Copyright (c) 2012, Joshua Graff
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

"""
Simple tree structure for representing a directory tree (in memory) and
then paths against that tree without re-stating the filesystem.
"""

"""
Change History

Version 0.6
  * Added support for skiping nodes and their children during visitation
    (raise TreeSkipNode)
  * Fixed validation in DirectoryTree so that an error is throw
    if path is valid for the tree but contains files or sub
    directories beyond that.
    
Version 0.5
  * Added support for writing tree to XML and creating tree from XML
  
Version 0.4
  * Added only_dirs (tree of directories only) option to DirectoryTree
  
Version 0.3
  * Remove whitespace from directory paths during validation
  
Version 0.2
  * Fixed DirectoryTree validate function
    + Added a number of unittests to cover failing cases.

Version 0.1
  * Initial Release
"""
__author__ = "Joshua Graff"
__version__ = "0.6"

import os
import sys
from xml.dom import minidom


class TreeNode(object):

    def __init__(self, value):
        self.value = value
        self._children = list()

    def add_child(self, value):
        if not isinstance(value, TreeNode):
            value = TreeNode(value)
        self._children.append(value)

    def has_children(self):
        return bool(self._children)

    def children(self):
        return self._children
    
    def __eq__(self, other):
        if isinstance(other, TreeNode):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "TreeNode('%s')" % str(self)

    
class TreeSkipNode(Exception): pass


class Tree(object):

    def __init__(self, root=None):
        if root and not isinstance(root, TreeNode):
            root = TreeNode(root)
        self.root = root
        self.depth = 0

    def walk(self, visit, node=None, depth=1):
        if node is None:
            node = self.root
        skip = False
        try:
            visit(node, depth)
        except TreeSkipNode:
            skip = True
        if not skip:
            for child in node.children():
                self.walk(visit, child, depth+1)

    def as_xml(self):
        impl = minidom.getDOMImplementation()
        doc = impl.createDocument(None, "Tree", None)
        parents = list()
        parents.append(doc.documentElement)
        def visit(node, depth):
            while depth < len(parents):
                parents.pop()
            element = doc.createElement('Node')
            element.setAttribute('value', str(node))
            parents[-1].appendChild(element)
            if node.children():
                parents.append(element)                
        self.walk(visit)
        return doc.toprettyxml()

    def from_xml(self, text):
        dom = minidom.parseString(text)
        def _create_tree(element, depth=1):
            node = TreeNode(element.getAttribute('value'))
            if depth > self.depth:
                self.depth = depth
            for child in element.childNodes:
                if child.nodeName != 'Node':
                    continue
                node.add_child(_create_tree(child, depth+1))
            return node
        self.root = _create_tree(dom.documentElement.childNodes[1])
        
    def as_text(self):
        """Display in ASCII text from left to right.

        E.x. 
          + root +
                 |
                 + Node_A +
                 |        |
                 |        + ChildNode_A
                 |        |
                 |        + ChildNode_B
                 |
                 + Node_B

        Nodes are represented as strings via their __str__ mdethod.
        """
        whitespace = list()
        lines = list()
        def visit(node, depth):
            value = str(node)
            value = '+ %s' % value
            if node.has_children():
                value = '%s +' % value
                
            while depth <= len(whitespace):
                whitespace.pop()
                
            # Put spacer if '|' in between each item
            columns = list()
            for idx, item in enumerate(whitespace):
                size, children = item
                if idx != 0:
                    size -= 1
                offset = ' ' * size
                if children:
                    columns.append('%s|' % offset)
                else:
                    columns.append('%s ' % offset)
            if columns:
                lines.append(''.join(columns))

            # Print value with optional leading '|'
            if not whitespace:
                lines.append(value)
            else:
                columns = list()
                for idx, item in enumerate(whitespace):
                    size, children = item
                    if idx != 0:
                        size -= 1
                    offset = ' ' * size                    
                    if idx == len(whitespace) - 1:
                        whitespace[idx][1] -= 1
                        columns.append('%s%s' % (offset, value))
                    else:
                        if children:
                            columns.append('%s|' % offset)
                        else:
                            columns.append('%s ' % offset)
                lines.append(''.join(columns))

            if node.has_children():
                #
                # Track whitespace depth for each node along with the
                # number of children seen.
                #
                # We decrement children seen on each visit, so that
                # we can skip '|' when there are no children left.
                #
                whitespace.append([(len(value) - 1), len(node.children())])

        self.walk(visit)
        return '\n'.join(lines)


class DirectoryTreeError(Exception): pass


class DirectoryTree(Tree):

    def __init__(self, path=None, max_depth=None, only_dirs=False):
        Tree.__init__(self)
        self.max_depth = max_depth
        if path and os.path.isfile(path):
            fd = open(path)
            try:
                self.from_xml(fd.read())
            finally:
                fd.close()
        elif path and os.path.isdir(path):
            self.from_dir(path, only_dirs=only_dirs)

    def from_dir(self, path, depth=1, only_dirs=False):
        def _create_tree(rootpath, depth):
            node = TreeNode(os.path.basename(rootpath))
            if depth > self.depth:
                self.depth = depth
            if os.path.isdir(rootpath) and depth != self.max_depth:
                for name in os.listdir(rootpath):
                    subpath = os.path.join(rootpath, name)
                    if only_dirs and os.path.isfile(subpath):
                        continue
                    child = _create_tree(subpath, depth+1)
                    node.add_child(child)
            return node
        self.root = _create_tree(path, depth)
            
    def validate(self, path):
        """Validate path against this tree and throw an exception if path
        is invalid.
        """
        path = os.path.normpath(path)
        parts = [part.strip() for part in path.split('/')]
        valid = list()
        if parts[0] != self.root:
            mesg = list()
            mesg.append("'%s' is not valid." % parts[0])
            mesg.append("Valid entries are:")
            mesg.append('  %s' % self.root)
            raise DirectoryTreeError('\n'.join(mesg))
        def visit(node, depth):
            if node != parts[depth-1]:
                raise TreeSkipNode
            valid.append(node.value)            
            if depth > (len(parts)-1):
                raise TreeSkipNode

            if node.children() and parts[depth] not in node.children():
                mesg = list()
                mesg.append("'%s' is not valid." % '/'.join(parts[:depth+1]))
                mesg.append("Valid entries are:")
                for child in node.children():
                    mesg.append('  %s/%s' % ('/'.join(parts[:depth]), child))
                raise DirectoryTreeError('\n'.join(mesg))
        self.walk(visit)
        if len(parts) > len(valid):
            mesg = list()
            mesg.append("'%s' is not a valid subdirectory or file in '%s'" %
                        ('/'.join(parts), '/'.join(valid)))
            raise DirectoryTreeError('\n'.join(mesg))
        return '/'.join(parts)


import tempfile
import shutil
import unittest
import textwrap


class TestDirectoryTree(unittest.TestCase):

    def setUp(self):
        self.scratch = tempfile.mkdtemp(dir='/tmp')

    def tearDown(self):
        shutil.rmtree(self.scratch)

    def create_simple_tree(self):
        """Create a simple single node tree.
        
        + root +
               |
               + a
        """
        os.makedirs(os.path.join(self.scratch, 'root', 'a'))
        return DirectoryTree(os.path.join(self.scratch, 'root'))

    def create_complex_tree(self, max_depth=None, only_dirs=False):
        """Create a complex multi node tree

        + root +
               |
               + dir_a +
               |       |
               |       + 1
               |       |
               |       + dir_b +
               |               |
               |               + 1
               |
               + dir_c +
               |       |
               |       + 1
               |
               + dir_d
        """
        os.makedirs(os.path.join(self.scratch, 'root', 'dir_a', 'dir_b'))
        os.makedirs(os.path.join(self.scratch, 'root', 'dir_c'))
        os.makedirs(os.path.join(self.scratch, 'root', 'dir_d'))
        fd = open(os.path.join(self.scratch, 'root', 'dir_a', '1'), 'w')
        fd.close()
        fd = open(os.path.join(self.scratch, 'root', 'dir_a', 'dir_b', '1'), 'w')
        fd.close()
        fd = open(os.path.join(self.scratch, 'root', 'dir_c', '1'), 'w')
        fd.close()
        return DirectoryTree(os.path.join(self.scratch, 'root'),
                             max_depth,
                             only_dirs=only_dirs)

    def test_simple_tree_dept(self):
        tree = self.create_simple_tree()
        self.assertEqual(tree.depth, 2, "Tree depth mismatch")

    def test_simple_tree_root(self):
        tree = self.create_simple_tree()
        self.assertEqual(tree.root, 'root',
                         "Tree root mismatch")

    def test_simple_tree_child(self):
        tree = self.create_simple_tree()
        self.assertEqual(tree.root.children()[0], 'a',
                         'Tree child mismatch')

    def test_simple_tree_valid(self):
        tree = self.create_simple_tree()
        tree.validate('root')
        tree.validate('root/a')

    def test_simple_tree_invalid(self):
        tree = self.create_simple_tree()
        self.assertRaises(DirectoryTreeError, tree.validate, "not-root")
        self.assertRaises(DirectoryTreeError, tree.validate, "root/b")
        self.assertRaises(DirectoryTreeError, tree.validate, "root/a/1")
        

    def test_simple_tree_as_text(self):
        tree = self.create_simple_tree()
        lines = self.create_simple_tree.__doc__.splitlines()
        text = '\n'.join(lines[2:])
        text = textwrap.dedent(text).strip()
        self.assertEqual(tree.as_text(), text)

    def test_complex_tree_as_text(self):
        tree = self.create_complex_tree()
        lines = self.create_complex_tree.__doc__.splitlines()
        text = '\n'.join(lines[2:])
        text = textwrap.dedent(text).strip()
        self.assertEqual(tree.as_text(), text)

    def test_complex_tree_as_xml(self):
        tree = self.create_complex_tree()
        xml = '<?xml version="1.0" ?>\n<Tree>\n\t<Node value="root">' \
              '\n\t\t<Node value="dir_a">\n\t\t\t<Node value="1"/>' \
              '\n\t\t\t<Node value="dir_b">\n\t\t\t\t<Node value="1"/>' \
              '\n\t\t\t</Node>\n\t\t</Node>\n\t\t<Node value="dir_c">' \
              '\n\t\t\t<Node value="1"/>\n\t\t</Node>\n\t\t' \
              '<Node value="dir_d"/>\n\t</Node>\n</Tree>\n'
        self.assertEqual(tree.as_xml(), xml, "XML output mismatch")

    def test_complex_tree_from_xml(self):
        xml = '<?xml version="1.0" ?>\n<Tree>\n\t<Node value="root">' \
              '\n\t\t<Node value="dir_a">\n\t\t\t<Node value="1"/>' \
              '\n\t\t\t<Node value="dir_b">\n\t\t\t\t<Node value="1"/>' \
              '\n\t\t\t</Node>\n\t\t</Node>\n\t\t<Node value="dir_c">' \
              '\n\t\t\t<Node value="1"/>\n\t\t</Node>\n\t\t' \
              '<Node value="dir_d"/>\n\t</Node>\n</Tree>\n'
        tree = DirectoryTree()
        tree.from_xml(xml)
        lines = self.create_complex_tree.__doc__.splitlines()
        text = '\n'.join(lines[2:])
        text = textwrap.dedent(text).strip()
        self.assertEqual(tree.as_text(), text)
        
    def test_complex_tree_max_depth(self):
        tree = self.create_complex_tree(2)
        self.assertEqual(tree.depth, 2)
        self.assertEqual(len(tree.root.children()), 3)

    def test_complex_tree_invalid(self):
        tree = self.create_complex_tree()
        self.assertRaises(DirectoryTreeError, tree.validate,
                          'root/dir_a/foo')
        self.assertRaises(DirectoryTreeError, tree.validate,
                          'root/dir_a/dir_b/2')
        self.assertRaises(DirectoryTreeError, tree.validate,
                          'root/dir_d/1')
        
    def test_complex_tree_valid(self):
        tree = self.create_complex_tree()
        tree.validate('root')
        tree.validate('root/dir_a')
        tree.validate('root/dir_a/1')
        tree.validate('root/dir_a/dir_b')
        tree.validate('root/dir_a/dir_b/1')

    def test_complex_tree_valid_limited_depth(self):
        tree = self.create_complex_tree(3)
        tree.validate('root')
        tree.validate('root/dir_a')
        tree.validate('root/dir_a/1')
        tree.validate('root/dir_a/dir_b')
        
    def test_complex_tree_only_dirs(self):
        tree = self.create_complex_tree(only_dirs=True)
        tree.validate('root')
        tree.validate('root/dir_a')
        self.assertRaises(DirectoryTreeError, tree.validate,
                          'root/dir_a/1')        
        tree.validate('root/dir_a/dir_b')

        
def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDirectoryTree)
    unittest.TextTestRunner(verbosity=2).run(suite)
    return 0

def display(path, depth):
    tree = DirectoryTree(path, depth)
    print tree.as_text()
    return 0

def xml(path, type, depth):
    if type == 'write':
        tree = DirectoryTree(path, depth)
        print tree.as_xml()
        return 0
    if type == 'read':
        tree = DirectoryTree(path, depth)
        print tree.as_text()
    
def usage(prog):
    print __doc__
    print "Usage: %s [display|test] [options]" % prog
    print "  display PATH [DEPTH]"
    print "    Graphical representation of PATH (default CWD) displayed to"
    print "    DEPTH."
    print
    print "  xml PATH [write|read] [DEPTH]"
    print "    If 'write' (default) dump an XML file of PATH and if 'read'"
    print "    display Graphical representation of XML file at PATH"
    print 
    print "  test"
    print "    Run unittests"
    return -1

def main(args):
    if len(args) < 2:
        return usage(args[0])
    if args[1] == 'test':
        return test()
    elif args[1] == 'display':
        path = os.getcwd()
        depth = None
        if len(args) >= 3:
            path = args[2]
        if len(args) >= 4:
            depth = int(args[3])
        return display(path, depth)
    elif args[1] == 'xml':
        path = os.getcwd()
        type = 'write'
        depth = None
        if len(args) >= 3:
            path = args[2]
        if len(args) >= 4:
            type = args[3]
        if len(args) >= 5:
            depth = args[4]
        return xml(path, type, depth)
    else:
        return usage(args[0])
    
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    

        
        
        
        
