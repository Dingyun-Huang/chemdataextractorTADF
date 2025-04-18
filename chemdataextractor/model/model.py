"""
Model classes for physical properties.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging


from .base import BaseModel, StringType, ListType, ModelType, SetType
from .units.temperature import TemperatureModel
from .units.length import LengthModel
from ..parse.cem import CompoundParser, \
    CompoundHeadingParser, ChemicalLabelParser, CompoundTableParser, names_only, ThemeCompoundParser, \
    labels_only, roles_only, chemical_name, ThemeChemicalLabelParser, ThemeCompoundTableParser
from ..parse.ir import IrParser
from ..parse.mp_new import MpParser
from ..parse.nmr import NmrParser
from ..parse.tg import TgParser
from ..parse.uvvis import UvvisParser
from ..parse.elements import R, I, Optional, W, Group, NoMatch, And, Not
from ..parse.actions import merge, join, fix_whitespace, fix_whitespaces_string
from ..model.units.quantity_model import QuantityModel, DimensionlessModel
from ..parse.auto import AutoTableParser, AutoSentenceParser
from ..parse.apparatus import ApparatusParser
from ..nlp import BertWordTokenizer

log = logging.getLogger(__name__)


class Compound(BaseModel):
    names = SetType(StringType(), parse_expression=names_only, updatable=True)
    labels = SetType(StringType(), parse_expression=NoMatch(), updatable=True)
    roles = SetType(StringType(), parse_expression=roles_only, updatable=True)
    parsers = [CompoundParser(), CompoundHeadingParser(), ChemicalLabelParser(), CompoundTableParser()]
    current_doc_compound = set()
    current_doc_compound_expressions = NoMatch()
    # parsers = [CompoundParser(), CompoundHeadingParser(), ChemicalLabelParser()]
    # parsers = [CompoundParser()]

    def merge(self, other):
        """Merge data from another Compound into this Compound."""
        log.debug('Merging: %s and %s' % (self.serialize(), other.serialize()))
        if type(other) != type(self):
            return self
        for k in self.keys():
            if other[k] is not None:
                if self[k] is not None:
                    for new_item in other[k]:
                        if new_item not in self[k]:
                            self[k].add(new_item)
        log.debug('Result: %s' % self.serialize())
        return self

    @property
    def is_unidentified(self):
        if not self.names and not self.labels:
            return True
        return False

    @property
    def is_id_only(self):
        """Return True if identifier information only."""
        for key, value in self.items():
            if key not in {'names', 'labels', 'roles'} and value:
                return False
        if self.names or self.labels:
            return True
        return False

    @classmethod
    def update(cls, definitions, strict=True):
        """Update the Compound labels parse expression

        Arguments:
            definitions {list} -- list of definitions found in this element
        """
        log.debug("Updating Compound")
        for definition in definitions:
            label = definition['label']
            if strict:
                new_label_expression = Group(W(label)('labels'))
            else:
                new_label_expression = Group(I(label)('labels'))
            if not cls.labels.parse_expression:
                cls.labels.parse_expression = new_label_expression
            else:
                cls.labels.parse_expression = cls.labels.parse_expression | new_label_expression
        return

    @classmethod
    def update_abbrev(cls, cem_abbreviation_definitions, strict=True):
        """Update the Compound name abbreviation parse expression

        Arguments:
            definitions {list} -- list of abbreviation definitions found in this element
        """
        log.debug("Updating Compound name abbreviations.")
        for definition in cem_abbreviation_definitions:
            short_tokens = definition[0]
            if strict:
                new_name_expression = W(short_tokens[0])
                for token in short_tokens[1:]:
                    new_name_expression = new_name_expression + W(token)
                new_name_expression = Group(new_name_expression).add_action(join).add_action(fix_whitespace)('names')
            else:
                new_name_expression = I(short_tokens[0])
                for token in short_tokens[1:]:
                    new_name_expression = new_name_expression + I(token)
                new_name_expression = Group(new_name_expression).add_action(join).add_action(fix_whitespace)('names')
            if not cls.current_doc_compound_expressions:
                cls.current_doc_compound_expressions = new_name_expression
            else:
                cls.current_doc_compound_expressions = new_name_expression | cls.current_doc_compound_expressions
        return


    @classmethod
    def reset_current_doc_compound(cls):
        cls.current_doc_compound = set()
        cls.current_doc_compound_expressions = NoMatch()

    def construct_label_expression(self, label):
        return W(label)('labels')

    @classmethod
    def construct_ordered_current_doc_compound_expressions(cls, strict=True):
        log.debug("Constructing current document compound expressions ordered with length.")
        ordered_set = sorted(cls.current_doc_compound, key=lambda t: len(t), reverse=True)
        cls.current_doc_compound_expressions = NoMatch()
        for tokens in ordered_set:
            if strict:
                new_name_expression = W(tokens[0])
                for token in tokens[1:]:
                    new_name_expression = new_name_expression + W(token)
                new_name_expression = Group(new_name_expression).add_action(join).add_action(fix_whitespace)('names')
            else:
                new_name_expression = I(tokens[0])
                for token in tokens[1:]:
                    new_name_expression = new_name_expression + I(token)
                new_name_expression = Group(new_name_expression).add_action(join).add_action(fix_whitespace)('names')
            if not cls.current_doc_compound_expressions:
                cls.current_doc_compound_expressions = new_name_expression
            else:
                cls.current_doc_compound_expressions = cls.current_doc_compound_expressions | new_name_expression
        return


class ThemeCompound(Compound):
    names = SetType(StringType(), parse_expression=NoMatch(), updatable=False)
    labels = SetType(StringType(), parse_expression=NoMatch(), updatable=False)
    roles = SetType(StringType(), parse_expression=NoMatch(), updatable=False)
    blocked_doi = False
    local_cems = []
    name_blocklist = ["\U0001F643"]
    label_blocklist = ['S1', '31G', 'S3', 'T1', '3LE', '3CT', 'V']
    parsers = [ThemeCompoundParser(), ThemeChemicalLabelParser(), ThemeCompoundTableParser()]

    @classmethod
    def update_theme_compound(cls, record_names, strict=True):
        """
        record_names {iterables} -- names to be updated into current_doc_compound_expressions
        """
        wt = BertWordTokenizer()
        for name in record_names:
            tokens = wt.tokenize(name)
            cls.current_doc_compound.add(tuple(tokens))
        cls.construct_ordered_current_doc_compound_expressions(strict=strict)
        return

    @classmethod
    def update_abbrev(cls, cem_abbreviation_definitions, strict=True):
        """Update the Compound name abbreviation parse expression excluding blocklisted names

        Arguments:
            definitions {list} -- list of abbreviation definitions found in this element
        """
        log.debug("Updating Compound name abbreviations.")
        for definition in cem_abbreviation_definitions:
            short_tokens = definition[0]
            long_tokens = definition[1]
            # blocklisted names and their abbreviations should not be added.
            if (fix_whitespaces_string(" ".join(short_tokens)) in cls.name_blocklist or
               fix_whitespaces_string(" ".join(long_tokens)) in cls.name_blocklist):
                continue
            cls.current_doc_compound.add(tuple(short_tokens))
        cls.construct_ordered_current_doc_compound_expressions(strict=strict)
        return

    @classmethod
    def reset_ThemeCompound_labels(cls):
        cls.labels.parse_expression = NoMatch()


class Apparatus(BaseModel):
    name = StringType()
    parsers = [ApparatusParser()]


class UvvisPeak(BaseModel):
    #: Peak value, i.e. wavelength
    value = StringType()
    #: Peak value units
    units = StringType(contextual=True)
    # Extinction value
    extinction = StringType()
    # Extinction units
    extinction_units = StringType(contextual=True)
    # Peak shape information (e.g. shoulder, broad)
    shape = StringType()


class UvvisSpectrum(BaseModel):
    solvent = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(UvvisPeak))
    compound = ModelType(Compound)
    parsers = [UvvisParser()]


class IrPeak(BaseModel):
    value = StringType()
    units = StringType(contextual=True)
    strength = StringType()
    bond = StringType()


class IrSpectrum(BaseModel):
    solvent = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(IrPeak))
    compound = ModelType(Compound)
    parsers = [IrParser()]


class NmrPeak(BaseModel):
    shift = StringType()
    intensity = StringType()
    multiplicity = StringType()
    coupling = StringType()
    coupling_units = StringType(contextual=True)
    number = StringType()
    assignment = StringType()


class NmrSpectrum(BaseModel):
    nucleus = StringType(contextual=True)
    solvent = StringType(contextual=True)
    frequency = StringType(contextual=True)
    frequency_units = StringType(contextual=True)
    standard = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(NmrPeak))
    compound = ModelType(Compound)
    parsers = [NmrParser()]

class MeltingPoint(TemperatureModel):
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    compound = ModelType(Compound, contextual=True)
    parsers = [MpParser()]


class GlassTransition(BaseModel):
    """A glass transition temperature."""
    value = StringType()
    units = StringType(contextual=True)
    method = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    compound = ModelType(Compound)
    parsers = [TgParser()]


class QuantumYield(BaseModel):
    """A quantum yield measurement."""
    value = StringType()
    units = StringType(contextual=True)
    solvent = StringType(contextual=True)
    type = StringType(contextual=True)
    standard = StringType(contextual=True)
    standard_value = StringType(contextual=True)
    standard_solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class FluorescenceLifetime(BaseModel):
    """A fluorescence lifetime measurement."""
    value = StringType()
    units = StringType(contextual=True)
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class ElectrochemicalPotential(BaseModel):
    """An oxidation or reduction potential, from cyclic voltammetry."""
    value = StringType()
    units = StringType(contextual=True)
    type = StringType(contextual=True)
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)

class NeelTemperature(TemperatureModel):
    # expression = (I('T')+I('N')).add_action(merge)
    expression = I('TN')
    # specifier = I('TN')
    specifier = StringType(parse_expression=expression, required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=False, contextual=False)


class CurieTemperature(TemperatureModel):
    # expression = (I('T') + I('C')).add_action(merge)
    expression = ((I('Curie') + R('^temperature(s)?$')) |  R('T[Cc]\d?')).add_action(join)
    specifier = StringType(parse_expression=expression, required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=False, contextual=False)


class InteratomicDistance(LengthModel):
    specifier_expression = (R('^bond$') + R('^distance')).add_action(merge)
    specifier = StringType(parse_expression=specifier_expression, required=False, contextual=True)
    rij_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    species = StringType(parse_expression=rij_label, required=True, contextual=False)
    compound = ModelType(Compound, required=True, contextual=True)
    another_label = StringType(parse_expression=R('^adgahg$'), required=False, contextual=False)


class CoordinationNumber(DimensionlessModel):
    # something like NTi-O will not work with this, only work if there is space between the label and specifier
    coordination_number_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    # specifier = (R('^(N|n|k)$') | (I('Pair') + I('ij')).add_action(merge)
    specifier_expression = R('^(N|n|k)$')
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=True)

    cn_label = StringType(parse_expression=coordination_number_label, required=True, contextual=True)
    compound = ModelType(Compound, required=True, contextual=True)


class CNLabel(BaseModel):
    # separate model to test automated parsing for stuff that are not quantities
    coordination_number_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    specifier = (I('Pair') + I('ij')).add_action(merge)
    label_Juraj = StringType(parse_expression=coordination_number_label)
    compound = ModelType(Compound, required=False)
    parsers = [AutoSentenceParser(), AutoTableParser()]

