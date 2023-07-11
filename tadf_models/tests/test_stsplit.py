import logging
import unittest
from chemdataextractor.doc import Sentence, Table, Caption
from tadf_models.models import STSplit, STSplitTableParser
from chemdataextractor.model import ThemeCompound
from chemdataextractor.parse.template import QuantityModelTemplateParser

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestSTSplitModel(unittest.TestCase):
    """Class for testing STSplit extraction"""

    def test_stsplit(self):
        """Test extracting stsplit model on a Sentence Object."""

        s = Sentence("As expected, compound 1 exhibited an ΔEST of 0.10 eV.")
        STSplit.parsers = [QuantityModelTemplateParser()]
        s.models = [STSplit]
        self.assertCountEqual(
            [{'STSplit': {'raw_value': '0.10',
                          'raw_units': 'eV',
                          'value': [0.1],
                          'units': 'ElectronVolt^(1.0)',
                          'specifier': 'ΔEST',
                          'compound': {'ThemeCompound': {'labels': ['1'], 'roles': ['nesting theme']}}}},
             {'ThemeCompound': {'labels': ['1'], 'roles': ['nesting theme']}}]
            ,
            s.records.serialize()
        )
        ThemeCompound.reset_ThemeCompound_labels()
        ThemeCompound.reset_current_doc_compound()
        ThemeCompound.reset_updatables()


    def test_STSplitTableParser(self):

        """Test the STSplitTableParser on a Table with header like S1/T1/ΔEST."""

        t = Table(caption=Caption("Table 1."), table_data=[["S1/T1/ΔEST [eV]"], ["3.14/2.86/0.28"]])
        STSplit.parsers = [STSplitTableParser()]
        t.models = [STSplit]
        self.assertEqual(
            [{'STSplit': {'raw_value': '0.28',
                          'raw_units': '[eV]',
                          'value': [0.28],
                          'units': 'ElectronVolt^(1.0)',
                          'specifier': 'ΔEST'}}]
            ,
            t.records.serialize()
        )
        ThemeCompound.reset_ThemeCompound_labels()
        ThemeCompound.reset_current_doc_compound()
        ThemeCompound.reset_updatables()


if __name__ == "__main__":
    unittest.main()
