API Reference
=============

This section documents the Python API for using epub2text as a library.

Core Classes
------------

EPUBParser
~~~~~~~~~~

.. autoclass:: epub2text.EPUBParser
   :members:
   :undoc-members:
   :show-inheritance:

Data Models
-----------

Chapter
~~~~~~~

.. autoclass:: epub2text.Chapter
   :members:
   :undoc-members:

Page
~~~~

.. autoclass:: epub2text.Page
   :members:
   :undoc-members:

PageSource
~~~~~~~~~~

.. autoclass:: epub2text.PageSource
   :members:
   :undoc-members:

Metadata
~~~~~~~~

.. autoclass:: epub2text.Metadata
   :members:
   :undoc-members:


Structured extraction
---------------------

StructuredEpubExtraction
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: epub2text.StructuredEpubExtraction
   :members:
   :undoc-members:

TextBlock
~~~~~~~~~

.. autoclass:: epub2text.TextBlock
   :members:
   :undoc-members:

TextSegment
~~~~~~~~~~~

.. autoclass:: epub2text.TextSegment
   :members:
   :undoc-members:

XhtmlFragment
~~~~~~~~~~~~~

.. autoclass:: epub2text.XhtmlFragment
   :members:
   :undoc-members:

ExtractionPolicy
~~~~~~~~~~~~~~~~

.. autoclass:: epub2text.ExtractionPolicy
   :members:
   :undoc-members:

extract_epub_structure
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: epub2text.extract_epub_structure
Bookmarks
---------

Bookmark
~~~~~~~~

.. autoclass:: epub2text.Bookmark
   :members:
   :undoc-members:

BookmarkManager
~~~~~~~~~~~~~~~

.. autoclass:: epub2text.BookmarkManager
   :members:
   :undoc-members:

Interactive Reader
------------------

EpubReader
~~~~~~~~~~

.. autoclass:: epub2text.EpubReader
   :members:
   :undoc-members:
   :show-inheritance:

ReaderState
~~~~~~~~~~~

.. autoclass:: epub2text.ReaderState
   :members:
   :undoc-members:

Text Cleaning
-------------

TextCleaner
~~~~~~~~~~~

.. autoclass:: epub2text.TextCleaner
   :members:
   :undoc-members:

clean_text
~~~~~~~~~~

.. autofunction:: epub2text.clean_text

Text Formatting
---------------

format_paragraphs
~~~~~~~~~~~~~~~~~

.. autofunction:: epub2text.formatters.format_paragraphs

format_sentences
~~~~~~~~~~~~~~~~

.. autofunction:: epub2text.formatters.format_sentences

format_clauses
~~~~~~~~~~~~~~

.. autofunction:: epub2text.formatters.format_clauses

split_long_lines
~~~~~~~~~~~~~~~~

.. autofunction:: epub2text.formatters.split_long_lines

collapse_paragraph
~~~~~~~~~~~~~~~~~~

.. autofunction:: epub2text.formatters.collapse_paragraph

split_paragraphs
~~~~~~~~~~~~~~~~

.. autofunction:: epub2text.formatters.split_paragraphs

Compatibility Function
----------------------

epub2txt
~~~~~~~~

.. autofunction:: epub2text.epub2txt

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

Parse an EPUB file and extract metadata::

    from epub2text import EPUBParser

    parser = EPUBParser("book.epub")

    # Get metadata
    metadata = parser.get_metadata()
    print(f"Title: {metadata.title}")
    print(f"Authors: {', '.join(metadata.authors)}")
    print(f"Language: {metadata.language}")

    # Get all chapters
    chapters = parser.get_chapters()
    for chapter in chapters:
        print(f"{chapter.title}: {chapter.char_count:,} characters")

    # Extract all text
    full_text = parser.extract_chapters()

Working with Pages
~~~~~~~~~~~~~~~~~~

Extract and work with pages::

    from epub2text import EPUBParser

    parser = EPUBParser("book.epub")

    # Check if EPUB has page-list navigation
    if parser.has_page_list():
        print("EPUB contains original page numbers")

    # Get pages (from page-list or generate synthetic pages)
    pages = parser.get_pages(synthetic_page_size=2000, use_words=False)

    for page in pages:
        print(f"Page {page.page_number}: {page.char_count} chars")
        print(f"  Source: {page.source.value}")
        print(f"  Chapter: {page.chapter_title}")

    # Extract text organized by pages
    page_text = parser.extract_pages(
        page_numbers=["1", "2", "3"],
        deduplicate_chapter_titles=True,
        skip_toc=True  # Skip table of contents
    )

Chapter Selection
~~~~~~~~~~~~~~~~~

Extract specific chapters::

    from epub2text import EPUBParser

    parser = EPUBParser("book.epub")
    chapters = parser.get_chapters()

    # Extract first 3 chapters
    chapter_ids = [chapters[0].id, chapters[1].id, chapters[2].id]
    text = parser.extract_chapters(chapter_ids)

Custom Text Cleaning
~~~~~~~~~~~~~~~~~~~~

Apply custom cleaning options::

    from epub2text import EPUBParser, TextCleaner

    parser = EPUBParser("book.epub")
    text = parser.extract_chapters()

    # Custom cleaning
    cleaner = TextCleaner(
        remove_footnotes=True,
        remove_page_numbers=True,
        normalize_whitespace=True,
        replace_single_newlines=True,
    )
    cleaned_text = cleaner.clean(text)

Sentence Formatting
~~~~~~~~~~~~~~~~~~~

Format text with one sentence per line::

    from epub2text import EPUBParser
    from epub2text.formatters import format_sentences

    parser = EPUBParser("book.epub")
    text = parser.extract_chapters()

    # One sentence per line
    formatted = format_sentences(text, separator="  ")

Clause Formatting
~~~~~~~~~~~~~~~~~

Format text with one clause per line::

    from epub2text import EPUBParser
    from epub2text.formatters import format_clauses

    parser = EPUBParser("book.epub")
    text = parser.extract_chapters()

    # One clause per line (split at commas, semicolons)
    formatted = format_clauses(text, separator="  ")

Line Splitting
~~~~~~~~~~~~~~

Split long lines at clause boundaries::

    from epub2text import EPUBParser
    from epub2text.formatters import split_long_lines

    parser = EPUBParser("book.epub")
    text = parser.extract_chapters()

    # Split lines exceeding 80 characters
    split_text = split_long_lines(text, max_length=80)

URL Support
~~~~~~~~~~~

Extract from EPUB files hosted online::

    from epub2text import epub2txt

    # Download and extract from URL
    text = epub2txt("https://example.com/book.epub")

    # Get list of chapters from URL
    chapters = epub2txt("https://example.com/book.epub", outputlist=True)

Bookmark Management
~~~~~~~~~~~~~~~~~~~

Manage reading bookmarks::

    from epub2text.bookmarks import BookmarkManager, Bookmark

    # Create bookmark manager (uses ~/.epub2text/bookmarks.json)
    manager = BookmarkManager()

    # Save bookmark
    bookmark = Bookmark.create(
        chapter_index=3,
        line_offset=150,
        percentage=45.5,
        title="My Book Title"
    )
    manager.save("/path/to/book.epub", bookmark)

    # Load bookmark
    bookmark = manager.load("/path/to/book.epub")
    if bookmark:
        print(f"Resume at {bookmark.percentage:.1f}%")

    # List all bookmarks
    all_bookmarks = manager.list_all()
    for path, bm in all_bookmarks.items():
        print(f"{bm.title}: {bm.percentage:.1f}%")

Full Metadata Access
~~~~~~~~~~~~~~~~~~~~

Access all Dublin Core metadata fields::

    from epub2text import EPUBParser

    parser = EPUBParser("book.epub")
    metadata = parser.get_metadata()

    print(f"Title: {metadata.title}")
    print(f"Authors: {metadata.authors}")
    print(f"Contributors: {metadata.contributors}")
    print(f"Publisher: {metadata.publisher}")
    print(f"Publication Year: {metadata.publication_year}")
    print(f"Identifier: {metadata.identifier}")
    print(f"Language: {metadata.language}")
    print(f"Rights: {metadata.rights}")
    print(f"Coverage: {metadata.coverage}")
    print(f"Description: {metadata.description}")

Module Index
------------

epub2text
~~~~~~~~~

Main package exports:

- ``EPUBParser`` - Main parser class
- ``Chapter`` - Chapter data model
- ``Page`` - Page data model
- ``PageSource`` - Page source enumeration
- ``Metadata`` - Metadata data model
- ``TextCleaner`` - Text cleaning class
- ``clean_text`` - Convenience function for text cleaning
- ``epub2txt`` - Compatibility function
- ``Bookmark`` - Bookmark data model
- ``BookmarkManager`` - Bookmark management class
- ``EpubReader`` - Interactive terminal reader
- ``ReaderState`` - Reader state data model

epub2text.formatters
~~~~~~~~~~~~~~~~~~~~

Text formatting utilities:

- ``format_paragraphs`` - Format text with paragraph separators
- ``format_sentences`` - One sentence per line formatting
- ``format_clauses`` - One clause per line formatting
- ``split_long_lines`` - Split long lines at clause boundaries
- ``split_paragraphs`` - Split text into paragraph list
- ``collapse_paragraph`` - Collapse paragraph to single line

epub2text.cleaner
~~~~~~~~~~~~~~~~~

Text cleaning utilities:

- ``TextCleaner`` - Configurable text cleaner class
- ``clean_text`` - Convenience function
- ``calculate_text_length`` - Calculate text length excluding markers

epub2text.bookmarks
~~~~~~~~~~~~~~~~~~~

Bookmark management:

- ``Bookmark`` - Bookmark data class
- ``BookmarkManager`` - Bookmark persistence manager

epub2text.reader
~~~~~~~~~~~~~~~~

Interactive terminal reader:

- ``EpubReader`` - Main reader class
- ``ReaderState`` - State information when reader exits
