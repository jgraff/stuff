manpage.py indentation fixes
============================

This ``manpage.py`` writer contains fixes for indentation with `Literal blocks`_
and Admonitions_.


Literal blocks
--------------

In the original writer literal blocks had the same indentation level as their
parent.

RST::

  =====
  Title
  =====
  
  :Version: 1.1
  :Author: joe.user@example.com
  
  
  Example
  =======
  
  Example::
  
    $ man ls

Man output::

  <snip>
  
  EXAMPLE
         Example:
  
         $ man ls
  
  <snip>

With this writer literal blocks are indented the same spacing as block quotes.

New man output::

  <snip>
  
  EXAMPLE
         Example:
  
            $ man ls
  
  <snip>


Admonitions
-----------

In the original writer admonitions used troff's ``.IP``/``.RE`` for paragraph 
indentation. This did not preserve indentation for bullets and other block
types (literal) that might be contained within an admonition.

RST::

  =====
  Title
  =====
  
  :Version: 1.1
  :Author: joe.user@example.com
  
  
  Example
  =======
  
  This is an example.
  
  .. NOTE::
     This is an important note.
  
     * Bullet
  
     Example::
  
       $ man ls

Man output::

  <snip>

  EXAMPLE
         This is an example.
  
         Note   This is an important note.
  
         o Bullet
  
         Example:
  
         $ man ls

  <snip>

With this writer admonitions are treated as block quotes with the admonition 
name in uppercase, strong, with a trailing ':'. 

New man output::

  <snip>

  EXAMPLE
         This is an example.
  
         NOTE:
            This is an important note.
  
            o Bullet
  
            Example:
  
                $ man ls

  <snip>
