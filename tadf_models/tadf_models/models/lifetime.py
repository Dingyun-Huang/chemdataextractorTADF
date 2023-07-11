from chemdataextractor.parse.elements import I, R, W, Optional, SkipTo, Group, NoMatch, OneOrMore, T
from chemdataextractor.parse.cem import cem, chemical_label, lenient_chemical_label
from chemdataextractor.parse.common import lbrct, rbrct
from chemdataextractor.parse import AutoTableParser, merge, join
from chemdataextractor.parse.template import MultiQuantityModelTemplateParser, \
    QuantityModelTemplateParser
from chemdataextractor.model import ModelType, StringType, FluorescenceLifetime
from chemdataextractor.model.units import TimeModel
from .condition import Temperature, RoomTemperature
from .wavelength import lamda_pl_specifier
from chemdataextractor.model import ThemeCompound
from chemdataextractor.parse.auto import value_element, match_dimensions_of, \
    create_entities_list
import logging
import six

log = logging.getLogger(__name__)

# Define specifiers for delayed lifetime and prompt lifetime.
tau = R("^[ττⲧ𝛕𝜏𝝉𝞃𝞽]$")
suffix_D = (R("^[Tt]1?\w?$") |  # for triplet
            R("^[Dd][Ff]\w?$") |
            R("^[Dd]elayed\w?$") |
            R("^[Dd]\w?$") | R("^[Tt]adf\w?$") | R("^TADF\w?$")
            )

TauD_specifier = ((tau + Optional(lbrct) + suffix_D + Optional(rbrct)).add_action(merge) |
                  # tau and suffix separated by space
                  R("^[ττⲧ𝛕𝜏𝝉𝞃𝞽]\(?((DF?)|(df?)|(tadf)|(TADF)|[Tt]|([Dd]elayed))\)?\w?$") |
                  # tau and suffix joined together
                  (((I("delayed") + Optional(R("^[Ff]luorescen((ce)|t)$"))) |
                    W("DF")) + (R("^[Ll]ifetimes?$") | R("^[cC]omponents?$"))).add_action(join) |
                  ((R("^[Ff]luorescen((ce)|t)$") | I("decay"))
                   + SkipTo(I("delayed")).hide() + I("delayed") + Optional(W("(") + I("DF") + W(")")) +
                   (R("^[Ll]ifetimes?$") | R("^components?$"))).add_action(join) |
                  (R("^[lL]ifetimes?$") + W("of") + SkipTo(W("delayed")).hide() + W("delayed") +
                   (W("fluorescence") | R("^components?$"))).add_action(join)
                  )


suffix_P = (R("^[Ss]\w?$") |  # for Singlet
            R("^[Ss]\w?$") |
            R("^[Pp][Ff]\w?$") |
            R("^[Pp]rompt\w?$") |
            R("^[Pp]\w?$")
            )

TauP_specifier = ((tau + Optional(lbrct) + suffix_P + Optional(rbrct)).add_action(merge) |
                  R("^[ττⲧ𝛕𝜏𝝉𝞃𝞽]\(?((PF?)|(pf?)|[Ss]|[Ff]|([Pp]rompt))\)?\w?$") |
                  (((I("prompt") + Optional(R("^[Ff]luorescen((ce)|t)$"))) | W("PF")) + (
                              R("^[Ll]ifetimes?$") | R("^[cC]omponents?$"))).add_action(join) |
                  ((R("^[Ff]luorescen((ce)|t)$") | I("decay"))
                   + SkipTo(I("delayed")).hide() + I("prompt") + Optional(W("(") + I("PF") + W(")")) + (
                               R("^[Ll]ifetimes?$") | R("^components?$"))).add_action(join) |
                  (R("^[lL]ifetimes?$") + W("of") + SkipTo(W("prompt")).hide() + W("prompt") + (
                              W("fluorescence") | R("^components?$"))).add_action(join)
                  )


# The following model was not used in the paper {doi}
#
#
# class PromptLifetime(TimeModel, FluorescenceLifetime):
#     specifier = StringType(parse_expression=TauP_specifier,
#                            required=True)
#     compound = ModelType(ThemeCompound, contextual=True, required=True, binding=True)
#     parsers = [MultiQuantityModelTemplateParser(),
#                QuantityModelTemplateParser(),
#                AutoTableParser(),
#                ]


def last(el):
    """
    :param el: Iterable
    :return: None if el is empy else return the last element of el.
    """
    if len(el) > 0:
        return el[-1]
    else:
        return None


def value_element(units=None):
    """
    Create a Parse element that can extract all sorts of values
    Fraction is removed in contrast to the original function in chemdataextractor.parse.quantity.
    """
    pure_number = R(r'^(([\+\-–−~∼˜]?\d+(([\.・,\d])+)?)|(\<nUm\>)|(×))+$')
    spaced_power_number = pure_number + R(r'^×$') + pure_number
    number = spaced_power_number | pure_number
    joined_range = R(r'^[\+\-–−~∼˜]?\d+(([\.・,\d])+)?[\-–−~∼˜]\d+(([\.・,\d])+)?$')('raw_value').add_action(merge)
    if units is not None:
        spaced_range = (number + Optional(units).hide() + (R(r'^[\-–−~∼˜]$') + number | number))('raw_value').add_action(merge)
        to_range = (number + Optional(units).hide() + I('to') + number)('raw_value').add_action(join)
    else:
        spaced_range = (number + R(r'^[\-–−~∼˜]$') + number)('raw_value').add_action(merge)
        to_range = (number + I('to') + number)('raw_value').add_action(join)
    plusminus_range = (number + R('±') + number)('raw_value').add_action(join)
    bracket_range = R('^' + '(\d+\.?(?:\d+)?)' + '\(\d+\)' + '$')('raw_value')
    spaced_bracket_range = (pure_number + W('(') + pure_number + W(')')).add_action(merge)('raw_value')
    between_range = (I('between').hide() + number + I('and') + number).add_action(join)
    value_range = (Optional(R('^[\-–−]$')) + (plusminus_range | joined_range | spaced_range | to_range | between_range | bracket_range | spaced_bracket_range))('raw_value').add_action(merge)
    value_single = (Optional(R('^[~∼˜\<\>]$')) + Optional(R('^[\-–−]$')) + number)('raw_value').add_action(merge)
    value = Optional(lbrct).hide() + (value_range | value_single)('raw_value') + Optional(rbrct).hide()
    if units is not None:
        value = value + units
    return value


class TauDTableParser(AutoTableParser):
    """ Additions for automated parsing of tables with column containing τp /τd, λem/nm(τd[μs]) etc."""

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
        no_value_element = (W('NoValue') | T('HYPH', tag_type="pos_tag"))('raw_value')

        # the special value elements for multientry table column are grouped into a entities list
        # print(self.model, self.model.dimensions)
        unit_element = Group((Optional(R("^[\(\[]$").hide()) + R("^[nmμ]?s$") +
                              Optional(R("^[\)\]]$").hide())).add_action(merge).with_condition(match_dimensions_of(self.model))(
                                'raw_units'))
        specifier = (((TauP_specifier + Optional(unit_element) + W("/")).hide() +
                     TauD_specifier('specifier') +
                     Optional(W('/')) + Optional((unit_element + W("/") + unit_element) | unit_element)) |
                    (lamda_pl_specifier + Optional(W("/")) + Optional(R("^[\(\[]$").hide())+ W("nm") +
                     Optional(R("^[\)\]]$").hide()) +
                     lbrct + TauD_specifier("specifier") + Optional(W("/")) + unit_element))

        value_phrase = (((value_element() | no_value_element) + Optional(unit_element)) +
                        (W("/") | W("|")) +
                        ((value_element() | no_value_element) + Optional(unit_element))) + Optional((W("/") | W("|")) +
                        ((value_element() | no_value_element) + Optional(unit_element)))

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
        raw_units = last(self._get_data_for_field(result, "raw_units", True))
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


class DelayedLifetime(TimeModel, FluorescenceLifetime):
    """
    Model for delayed lifetime
    """
    specifier = StringType(parse_expression=TauD_specifier,
                           required=True)
    compound = ModelType(ThemeCompound, contextual=True, required=False, binding=False)
    temperature = ModelType(Temperature, required=False, contextual=False)
    room_temperature = ModelType(RoomTemperature)
    parsers = [MultiQuantityModelTemplateParser(),
               QuantityModelTemplateParser(),
               TauDTableParser(),
               AutoTableParser(),
               ]

