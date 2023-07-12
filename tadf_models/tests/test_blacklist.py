from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest
from chemdataextractor.doc import Sentence
from chemdataextractor.model import ThemeCompound, Compound
import importlib.resources

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

ThemeCompound.name_blacklist = []
tadf_blacklist = importlib.resources.read_text(
    'tadf_models', 'tadf_blacklist_6_more_abbrev_enriched', encoding='utf-8')
elements = importlib.resources.read_text('tadf_models', 'elements')
tadf_blacklist = tadf_blacklist.split('\n')
elements = elements.split('\n')
ThemeCompound.name_blacklist = ThemeCompound.name_blacklist + tadf_blacklist + elements


class TestBlacklist(unittest.TestCase):

    def test_compound(self):
        """Test the the default Compound model."""
        s = Sentence(
            "Compound 1 in N2 exhibits a delayed fluorescence lifetime of 4 μs.")
        s.models = [Compound]
        self.assertCountEqual(
            [{'Compound': {'labels': ['1'], 'roles': ["compound"]}},
                {'Compound': {'labels': ["N2"]}}],
            s.records.serialize()
        )

    def test_blacklist(self):
        """Test the blacklisting mechanism"""
        s = Sentence(
            "Compound 1 in N2 exhibits a delayed fluorescence lifetime of 4 μs.")
        s.models = [ThemeCompound]
        self.assertCountEqual(
            [{'ThemeCompound': {'labels': ['1'], 'roles': ['nesting theme']}}],
            s.records.serialize()
        )
        ThemeCompound.reset_ThemeCompound_labels()
        ThemeCompound.reset_current_doc_compound()
        ThemeCompound.reset_updatables()


if __name__ == "__main__":
    unittest.main()
