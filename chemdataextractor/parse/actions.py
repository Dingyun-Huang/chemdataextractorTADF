# -*- coding: utf-8 -*-
"""
Actions to perform during parsing.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re

from lxml.builder import E
from lxml.etree import strip_tags

from ..text import HYPHENS


log = logging.getLogger(__name__)


def flatten(tokens, start, result):
    """Replace all child results with their text contents."""
    for e in result:
        strip_tags(e, '*')
    return result


def join(tokens, start, result):
    """Join tokens into a single string with spaces between."""
    texts = []
    if len(result) > 0:
        for e in result:
            for child in e.iter():
                if child.text is not None:
                    texts.append(child.text)
        return [E(result[0].tag, ' '.join(texts))]


def merge(tokens, start, result):
    """Join tokens into a single string with no spaces."""
    texts = []
    if len(result) > 0:
        for e in result:
            for child in e.iter():
                if child.text is not None:
                    texts.append(child.text)
        return [E(result[0].tag, ''.join(texts))]


def strip_stop(tokens, start, result):
    """Remove trailing full stop from tokens."""
    for e in result:
        for child in e.iter():
            if child.text.endswith('.'):
                child.text = child.text[:-1]
    return result


def fix_whitespace(tokens, start, result):
    """Fix whitespace around hyphens and commas. Can be used to remove whitespace tokenization artefacts."""
    for e in result:
        for child in e.iter():
            # if check added by Juraj, it has to exist
            if child.text:
                child.text = child.text.replace(' , ', ', ').replace(' ,', ',')
                for hyphen in HYPHENS:
                    child.text = child.text.replace('%s ' % hyphen, '%s' % hyphen).replace(' %s' % hyphen, '%s' % hyphen)
                child.text = re.sub(r'- (.) -', r'-\1-', child.text)
                child.text = child.text.replace(" -", "-")
                child.text = child.text.replace(" : ", ":").replace(" ) ", ")")

                child.text = child.text.replace(" ( ", "(").replace(" ) ", ")")
                child.text = child.text.replace(" / ", "/")
                child.text = child.text.replace(" [ ", "[").replace(" ] ", "]")
                child.text = child.text.replace("( ", "(").replace(" )", ")")
                child.text = child.text.replace("[ ", "[").replace(" ]", "]")
                child.text = child.text.replace("′ ", "′").replace(" ′", "′")
    return result


def fix_whitespaces_string(string_result):
    """Fix whitespace around hyphens and commas. Can be used to remove whitespace tokenization artefacts."""

    string_result = string_result.replace(' , ', ', ').replace(' ,', ',')
    for hyphen in HYPHENS:
        string_result = string_result.replace('%s ' % hyphen, '%s' % hyphen).replace(' %s' % hyphen, '%s' % hyphen)
    string_result = re.sub(r'- (.) -', r'-\1-', string_result)
    string_result = string_result.replace(" -", "-")
    string_result = string_result.replace(" ( ", "(").replace(" ) ", ")")
    string_result = string_result.replace(" / ", "/")
    string_result = string_result.replace(" [ ", "[").replace(" ] ", "]")
    string_result = string_result.replace("( ", "(").replace(" )", ")")
    string_result = string_result.replace("[ ", "[").replace(" ]", "]")
    string_result = string_result.replace("′ ", "′").replace(" ′", "′")
    string_result = string_result.replace(", ", ",").replace(" ,", ",")
    return string_result
