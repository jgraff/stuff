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

Version 0.2
  * Fixed DirectoryTree validate function
    + Added a number of unittests to cover failing cases.

Version 0.1
  * Initial Release
"""
__author__ = "Joshua Graff"
__version__ = "0.2"

import os
import sys


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

    
class Tree(object):

    def __init__(self, root=None):
        if root and not isinstance(root, TreeNode):
            root = TreeNode(root)
        self.root = root
        self.depth = 0

    def walk(self, visit, node=None, depth=1):
        if node is None:
            node = self.root
        visit(node, depth)
        if node.children():
            for child in node.children():
                self.walk(visit, child, depth+1)

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

    def __init__(self, path, max_depth=None):
        Tree.__init__(self)
        self.max_depth = max_depth
        if not os.path.exists(path):
            raise DirectoryTreeError("'%s' does not exist" % path)
        self.root = self.create_tree(path)

    def create_tree(self, rootpath, depth=1):
        node = TreeNode(os.path.basename(rootpath))
        if depth > self.depth:
            self.depth = depth
        if os.path.isdir(rootpath) and depth != self.max_depth:
            for name in os.listdir(rootpath):
                path = os.path.join(rootpath, name)
                node.add_child(self.create_tree(path, depth+1))
        return node

    def validate(self, path):
        """Validate path against this tree and throw an exception if path
        is invalid.
        """
        path = os.path.normpath(path)
        parts = path.split('/')
        if parts[0] != self.root:
            mesg = list()
            mesg.append("'%s' is not valid." % parts[0])
            mesg.append("Valid entries are:")
            mesg.append('  %s' % self.root)
            raise DirectoryTreeError('\n'.join(mesg))
        def visit(node, depth):
            if depth > (len(parts)-1) or node != parts[depth-1]:
                return
            if node.children() and parts[depth] not in node.children():
                mesg = list()
                mesg.append("'%s' is not valid." % '/'.join(parts[:depth+1]))
                mesg.append("Valid entries are:")
                for child in node.children():
                    mesg.append('  %s/%s' % ('/'.join(parts[:depth]), child))
                raise DirectoryTreeError('\n'.join(mesg))
        self.walk(visit)
        return path

        
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

    def create_complex_tree(self, max_depth=None):
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
        return DirectoryTree(os.path.join(self.scratch, 'root'), max_depth)

    def test_path_does_not_exist(self):
        self.assertRaises(DirectoryTreeError, DirectoryTree,
                          os.path.join(self.scratch, 'root'))
        
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

    def test_simple_tree_display(self):
        tree = self.create_simple_tree()
        lines = self.create_simple_tree.__doc__.splitlines()
        text = '\n'.join(lines[2:])
        text = textwrap.dedent(text).strip()
        self.assertEqual(tree.as_text(), text)

    def test_complex_tree_display(self):
        tree = self.create_complex_tree()
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

    def test_complex_tree_valid(self):
        tree = self.create_complex_tree()
        tree.validate('root')
        tree.validate('root/dir_a')
        tree.validate('root/dir_a/1')
        tree.validate('root/dir_a/dir_b')
        tree.validate('root/dir_a/dir_b/1')

    def test_complex_tree_valid_limited_depth(self):
        tree = self.create_complex_tree(2)
        tree.validate('root')
        tree.validate('root/dir_a')
        tree.validate('root/dir_a/1')
        tree.validate('root/dir_a/dir_b')
        tree.validate('root/dir_a/dir_b/1')
        
        
def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDirectoryTree)
    unittest.TextTestRunner(verbosity=2).run(suite)
    return 0

def display(path, depth):
    tree = DirectoryTree(path, depth)
    print tree.as_text()
    return 0

def usage(prog):
    print __doc__
    print "Usage: %s [display|test] [options]" % prog
    print "  display PATH [DEPTH] : Graphical representation of PATH"
    print "                         (default CWD) displayed to DEPTH."
    print
    print "  test : Run unittests"
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
    else:
        return usage(args[0])
    
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    

        
        
        
        
