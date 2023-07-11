from chemdataextractor.parse.elements import I, R, W, Optional, T, Group, NoMatch, OneOrMore, SkipTo
from chemdataextractor.parse.actions import merge
from chemdataextractor.parse import AutoTableParser
from chemdataextractor.parse.template import MultiQuantityModelTemplateParser, \
    QuantityModelTemplateParser
from chemdataextractor.model import ModelType, StringType
from chemdataextractor.model.units import EnergyModel
from chemdataextractor.parse.cem import cem, chemical_label, lenient_chemical_label
from chemdataextractor.model import ThemeCompound
from chemdataextractor.parse.auto import construct_unit_element, value_element, match_dimensions_of, \
    create_entities_list
from chemdataextractor.utils import first
import logging
import six

log = logging.getLogger(__name__)

# Define specifier for Singlet-Triplet split
delta_E = R("^[Δⲇ𝜟𝝙𝛥𝞓𝚫∆Ⲇ]E$")
suffix_total = (R("^(ST)|(st)\w{0,2}$") | R("^[Ss][-‐‑⁃‒–—―-][Tt]\w{0,2}$"))

stsplit_specifier = ((delta_E + suffix_total).add_action(merge) |
                     (I("singlet") + Optional(T('HYPH', tag_type="pos_tag") | W("/")) + I("Triplet") + R(
                         "^[Ss]plit(tings?)?$")) |
                     R("^[Δⲇ𝜟𝝙𝛥𝞓𝚫∆Ⲇ]E((ST)|(st))\w{0,2}$") |
                     (R("^[Δⲇ𝜟𝝙𝛥𝞓𝚫∆Ⲇ]E[Ss]$") + T('HYPH', tag_type="pos_tag") + R("^[Tt]\w{0,2}$")).add_action(merge)
                     )


def last(el):
    """
    :param el: Iterable
    :return: None if el is empy else return the last element of el.
    """
    if len(el) > 0:
        return el[-1]
    else:
        return None


class STSplitTableParser(AutoTableParser):
    """ Additions for automated parsing of tables with column containing S1/T1/ΔST"""

    def __init__(self, chem_name=(cem | chemical_label | lenient_chemical_label)):
        super(AutoTableParser, self).__init__()
        self.chem_name = chem_name

    @property
    def root(self):
        # is always found, our models currently rely on the compound
        try:
            current_doc_compound_expressions = self.model.compound.model_class.current_doc_compound_expressions
            chem_name = Group(current_doc_compound_expressions)('compound') | self.chem_name
        except AttributeError:
            # the model does not require a compound
            chem_name = NoMatch()

        try:
            compound_model = self.model.compound.model_class
            labels = Group(compound_model.labels.parse_expression('labels'))('compound')
            if compound_model.__name__ == 'ThemeCompound':
                chem_name = compound_model.parsers[0].root.expr
        except AttributeError:
            labels = NoMatch()
        entities = [labels]
        no_value_element = W('NoValue')('raw_value')

        # the special value elements for multientry table column are grouped into a entities list
        # print(self.model, self.model.dimensions)
        unit_element = Group(
            construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))(
                'raw_units'))
        specifier = ((R("^[(S1)(ES1?)]\w?$") + W("/") + R("^[(T1)(ET1?)]\w?$") + W("/")).hide() +
                    stsplit_specifier('specifier') +
                    Optional(W('/')) + Optional(unit_element))

        value_phrase = (((value_element() | no_value_element) + Optional(unit_element)) +
                        W("/") +
                        ((value_element() | no_value_element) + Optional(unit_element)) +
                        W("/") +
                        ((value_element() | no_value_element) + Optional(unit_element))
                        )
        entities.append(specifier)
        entities.append(value_phrase)

        # the optional, user-defined, entities of the model are added, they are tagged with the name of the field
        for field in self.model.fields:
            if field not in ['raw_value', 'raw_units', 'value', 'units', 'error', 'specifier']:
                if self.model.__getattribute__(self.model, field).parse_expression is not None:
                    entities.append(self.model.__getattribute__(self.model, field).parse_expression(field))

        # the chem_name has to be parsed last in order to avoid a conflict with other elements of the model
        entities.append(chem_name)

        # logic for finding all the elements in any order
        combined_entities = create_entities_list(entities)
        root_phrase = OneOrMore(combined_entities + Optional(SkipTo(combined_entities)))('root_phrase')
        return root_phrase

    def interpret(self, result, start, end):
        # print(etree.tostring(result))
        if result is None:
            return
        property_entities = {}

        # the specific entities of a QuantityModel are retrieved explicitly and packed into a dictionary
        # print(etree.tostring(result))
        raw_value = last(self._get_data_for_field(result, "raw_value", True))
        raw_units = first(self._get_data_for_field(result, "raw_units", True))
        property_entities.update({"raw_value": raw_value,
                                  "raw_units": raw_units})

        for field_name, field in six.iteritems(self.model.fields):
            if field_name not in ['raw_value', 'raw_units', 'value', 'units', 'error']:
                try:
                    data = self._get_data(field_name, field, result)
                    if data is not None:
                        property_entities.update(data)
                # if field is required, but empty, the requirements have not been met
                except TypeError as e:
                    log.debug(self.model)
                    log.debug(e)

        model_instance = None
        if property_entities.keys():
            model_instance = self.model(**property_entities)

        if model_instance and model_instance.noncontextual_required_fulfilled:
            # records the parser that was used to generate this record, can be used for evaluation
            model_instance.record_method = self.__class__.__name__
            yield model_instance


class STSplit(EnergyModel):
    """
    Model for Singlet-Triplet split.
    """
    specifier = StringType(parse_expression=stsplit_specifier,
                           required=True)
    compound = ModelType(ThemeCompound, contextual=True, required=False, binding=False)
    parsers = [MultiQuantityModelTemplateParser(),
               QuantityModelTemplateParser(),
               STSplitTableParser(),
               AutoTableParser(),
               ]
