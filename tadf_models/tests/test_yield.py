from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import unittest

from chemdataextractor.doc.document import Document
from chemdataextractor.doc import Paragraph, Sentence, Table, Caption
from chemdataextractor.model import ThemeCompound
from tadf_models.models import PhotoluminescenceQuantumYield, DimlessPLQYTableParser

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestPLQYModels(unittest.TestCase):

    def test_Photoluminescence_abbreviation_specifier(self):
        """Test the extracting photoluminescence quantum model on a Sentence Object with abbreviation specifer."""
        s = Sentence("Compound 1 showed the highest PLQY of 24.1%.")
        s.models = [PhotoluminescenceQuantumYield]
        self.assertCountEqual(
            [{'ThemeCompound': {'labels': ['1'], 'roles': ['nesting theme']}},
             {'PhotoluminescenceQuantumYield': {'compound': {'ThemeCompound': {'labels': ['1'],
                                                                          'roles': ['nesting theme']}},
                                                'raw_units': '%',
                                                'raw_value': '24.1',
                                                'specifier': 'PLQY',
                                                'units': 'Percent^(1.0)',
                                                'value': [24.1]}}]
            ,
            s.records.serialize()
        )
        ThemeCompound.reset_ThemeCompound_labels()
        ThemeCompound.reset_current_doc_compound()
        ThemeCompound.reset_updatables()

    def test_Photoluminescence_PL_specifier(self):
        """Test the extracting photoluminescence quantum model on a Sentence Object with abbreviation specifer."""
        s = Sentence("PL quantum yield of 24.1%.")
        PhotoluminescenceQuantumYield.compound.required = False
        s.models = [PhotoluminescenceQuantumYield]
        self.assertEqual(
            [{'PhotoluminescenceQuantumYield': {'raw_units': '%',
                                                'raw_value': '24.1',
                                                'specifier': 'PL quantum yield',
                                                'units': 'Percent^(1.0)',
                                                'value': [24.1]}}]
            ,
            s.records.serialize()
        )

    def test_Photoluminescence_symbolic_specifier(self):
        """Test the extracting photoluminescence quantum model on a Sentence Object with abbreviation specifer."""
        s = Sentence("ΦPL of 24.1%.")
        PhotoluminescenceQuantumYield.compound.required = False
        s.models = [PhotoluminescenceQuantumYield]
        self.assertEqual(
            [{'PhotoluminescenceQuantumYield': {'raw_units': '%',
                                                'raw_value': '24.1',
                                                'specifier': 'ΦPL',
                                                'units': 'Percent^(1.0)',
                                                'value': [24.1]}}]
            ,
            s.records.serialize()
        )

    def test_Photoluminescence_symbolic_specifier_with_space(self):
        """Test the extracting photoluminescence quantum model on a Sentence Object with abbreviation specifer."""
        s = Sentence("Φ PL of 24.1%.")
        PhotoluminescenceQuantumYield.compound.required = False
        s.models = [PhotoluminescenceQuantumYield]
        self.assertEqual(
            [{'PhotoluminescenceQuantumYield': {'raw_units': '%',
                                                'raw_value': '24.1',
                                                'specifier': 'ΦPL',
                                                'units': 'Percent^(1.0)',
                                                'value': [24.1]}}]
            ,
            s.records.serialize()
        )

    def test_DimlessPLQYTableParser(self):
        """Test the TauDTableParser on a Table with header like τp/τd [unit]."""
        d = Document(Table(caption=Caption("Table 1."), table_data=[["Φ PL"], ["0.45"]]))
        # PhotoluminescenceQuantumYield.parsers = [DimlessPLQYTableParser()]
        d.models = [PhotoluminescenceQuantumYield]
        self.assertEqual(
            [{'PhotoluminescenceQuantumYield': {'raw_value': '0.45×102',
                                  'raw_units': '%',
                                  'value': [45.0],
                                  'units': 'Percent^(1.0)',
                                  'specifier': 'ΦPL'}}]
            ,
            d.records.serialize()
        )


if __name__ == "__main__":
    unittest.main()