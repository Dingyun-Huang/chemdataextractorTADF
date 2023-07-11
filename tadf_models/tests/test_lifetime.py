from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest
from chemdataextractor.doc import Paragraph, Sentence, Table, Caption
from tadf_models.models import DelayedLifetime, TauDTableParser
from chemdataextractor.model import ThemeCompound

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestLifetimeModel(unittest.TestCase):


    def test_DelayedLifetime_full_specifier(self):
        """Test the extracting PromptLifetime model on a Sentence Object with letter specifer."""
        s = Sentence("Compound 1 exhibits a delayed fluorescence lifetime of 4 μs.")
        s.models = [DelayedLifetime]
        self.assertCountEqual(
            [{'ThemeCompound': {'labels': ['1'], 'roles': ['nesting theme']}},
             {'DelayedLifetime': {'raw_value': '4',
                                 'raw_units': 'μs',
                                 'value': [4.0],
                                 'units': '(10^-6.0) * Second^(1.0)',
                                 'specifier': 'delayed fluorescence lifetime',
                                 'compound': {'ThemeCompound': {'labels': ['1'], 'roles': ['nesting theme']}}}}]
            ,
            s.records.serialize()
        )
        ThemeCompound.reset_ThemeCompound_labels()
        ThemeCompound.reset_current_doc_compound()
        ThemeCompound.reset_updatables()


    def test_DelayedLifetime_letter_specifier(self):
        """Test the extracting PromptLifetime model on a Sentence Object with letter specifer."""
        s = Sentence("τ(TADF) of 120 μs.")
        s.models = [DelayedLifetime]
        self.assertEqual(
            [{'DelayedLifetime': {'raw_value': '120',
                                  'raw_units': 'μs',
                                  'value': [120.0],
                                  'units': '(10^-6.0) * Second^(1.0)',
                                  'specifier': 'τTADF'}}]
            ,
            s.records.serialize()
        )

    def test_DelayedLifetime_letter_specifier_with_space(self):
        """Test the extracting PromptLifetime model on a Sentence Object with letter specifer."""
        s = Sentence("τ TADF of 120 μs.")
        s.models = [DelayedLifetime]
        self.assertEqual(
            [{'DelayedLifetime': {'raw_value': '120',
                                  'raw_units': 'μs',
                                  'value': [120.0],
                                  'units': '(10^-6.0) * Second^(1.0)',
                                  'specifier': 'τTADF'}}]
            ,
            s.records.serialize()
        )

    def test_TauDTableParser_1(self):
        """Test the TauDTableParser on a Table with header like τp/τd [unit]."""
        t = Table(caption=Caption("Table 1."), table_data=[["τp/τd [ns]"], ["145/3100"]])
        DelayedLifetime.parsers = [TauDTableParser()]
        t.models = [DelayedLifetime]
        self.assertEqual(
            [{'DelayedLifetime': {'raw_value': '3100',
                          'raw_units': 'ns',
                          'value': [3100.0],
                          'units': '(10^-9.0) * Second^(1.0)',
                          'specifier': 'τd'}}]
            ,
            t.records.serialize()
        )

    def test_TauDTableParser_2(self):
        """Test the TauDTableParser on a Table with header like τp [ns] /τd [μs]."""
        t = Table(caption=Caption("Table 1."), table_data=[["τp [ns]/τd [μs]"], ["145/3.1"]])
        DelayedLifetime.parsers = [TauDTableParser()]
        t.models = [DelayedLifetime]
        self.assertEqual(
            [{'DelayedLifetime': {'raw_value': '3.1',
                          'raw_units': 'μs',
                          'value': [3.1],
                          'units': '(10^-6.0) * Second^(1.0)',
                          'specifier': 'τd'}}]
            ,
            t.records.serialize()
        )

    def test_TauDTableParser_3(self):
        """Test the TauDTableParser on a Table with header like τp /τd."""
        t = Table(caption=Caption("Table 1."), table_data=[["τp /τd"], ["145 [ns]/3.1 [μs]"]])
        DelayedLifetime.parsers = [TauDTableParser()]
        t.models = [DelayedLifetime]
        self.assertEqual(
            [{'DelayedLifetime': {'raw_value': '3.1',
                          'raw_units': 'μs',
                          'value': [3.1],
                          'units': '(10^-6.0) * Second^(1.0)',
                          'specifier': 'τd'}}]
            ,
            t.records.serialize()
        )

    def test_TauDTableParser_4(self):
        """Test the TauDTableParser on a Table with header like τp /τd [ns/μs]."""
        t = Table(caption=Caption("Table 1."), table_data=[["τp/τd [ns/μs]"], ["145/3.1"]])
        DelayedLifetime.parsers = [TauDTableParser()]
        t.models = [DelayedLifetime]
        self.assertEqual(
            [{'DelayedLifetime': {'raw_value': '3.1',
                          'raw_units': 'μs',
                          'value': [3.1],
                          'units': '(10^-6.0) * Second^(1.0)',
                          'specifier': 'τd'}}]
            ,
            t.records.serialize()
        )

    def test_TauDTableParser_5(self):
        """Test the TauDTableParser on a Table with header like λem/nm(τd[μs])."""
        t = Table(caption=Caption("Table 1."), table_data=[["λem/nm(τd[μs])"], ["521/3.1"]])
        DelayedLifetime.parsers = [TauDTableParser()]
        t.models = [DelayedLifetime]
        self.assertEqual(
            [{'DelayedLifetime': {'raw_value': '3.1',
                          'raw_units': 'μs',
                          'value': [3.1],
                          'units': '(10^-6.0) * Second^(1.0)',
                          'specifier': 'τd'}}]
            ,
            t.records.serialize()
        )

    def test_TauDTableParser_6(self):
        """Test the TauDTableParser on a Table with header like λem/nm(τd[μs])."""
        t = Table(caption=Caption("Table 1."), table_data=[["λmax[nm](τd/μs)"], ["521/3.1"]])
        DelayedLifetime.parsers = [TauDTableParser()]
        t.models = [DelayedLifetime]
        self.assertEqual(
            [{'DelayedLifetime': {'raw_value': '3.1',
                          'raw_units': 'μs',
                          'value': [3.1],
                          'units': '(10^-6.0) * Second^(1.0)',
                          'specifier': 'τd'}}]
            ,
            t.records.serialize()
        )


if __name__ == "__main__":
    unittest.main()
