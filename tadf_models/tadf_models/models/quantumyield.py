from chemdataextractor.model import QuantumYield
from chemdataextractor.model.units import RatioModel
from chemdataextractor.parse.elements import I, R, W, Optional, ZeroOrMore, Any
from chemdataextractor.parse import AutoTableParser, merge, join
from chemdataextractor.parse.template import MultiQuantityModelTemplateParser, \
    QuantityModelTemplateParser
from chemdataextractor.model import ModelType, StringType
from chemdataextractor.model import ThemeCompound
from chemdataextractor.parse.cem import cem, chemical_label, lenient_chemical_label
import re
from chemdataextractor.utils import first
import logging
import six
from .condition import room_temperature_expression, Temperature, Phase, Atmosphere

log = logging.getLogger(__name__)

# Define specifiers for various quantum yields.
phi = R("^[𝛷𝟇ɸ𝛗𝜱𝝋𝛟ΦⲪᶲ𝝫ᵩ𝜙𝚽φ𝞥𝞍𝝓𝜑ⲫϕᵠ]$")
suffix_total = (R("^[Pp][Ll]\w?$") | R("^[Tt]otal\w?$") | R("^[Ee][Mm]\w?$") | R("^(PL)?QY\w?$") +
                ZeroOrMore(Any()) + W("%"))

PLQY_specifier = ((phi + suffix_total).add_action(merge) |
                  R("^PLQY") | R("^IQY$") |
                  (Optional(W("internal")) + (I("photoluminescence") | W("PL")) + I("quantum") + I("yield")).add_action(join) | phi |
                  R("^[ΦϕφⲪⲫɸ𝟇𝞥𝞍𝝫𝝓𝜱𝜙𝛷𝛟𝚽ᶲ](([Pp][Ll])|([Ee][Mm]))([Aa]ir)?(inert)?([Vv]ac)?\w?$")
                  )


class DimlessPLQYTableParser(AutoTableParser):
    """ Additions for automated parsing of tables
    with column containing PLQY in decimals less than one instead of percentage"""

    def __init__(self, chem_name=(cem | chemical_label | lenient_chemical_label)):
        super(AutoTableParser, self).__init__()
        self.chem_name = chem_name

    def interpret(self, result, start, end):
        # print(etree.tostring(result))
        if result is None:
            return
        property_entities = {}

        # the specific entities of a QuantityModel are retrieved explicitly and packed into a dictionary
        # print(etree.tostring(result))
        raw_value = first(self._get_data_for_field(result, "raw_value", True))
        raw_units = first(self._get_data_for_field(result, "raw_units", True))
        # If a unit was found then leave the record to AutoTableParser to avoid duplicates.
        if raw_units:
            return
        if re.compile("0\.\d{1,3}$").findall(str(raw_value)):
            raw_value = raw_value + "×102"
        else:
            return
        property_entities.update({"raw_value": raw_value,
                                  "raw_units": "%"})

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


class PhotoluminescenceQuantumYield(RatioModel, QuantumYield):
    """
    Model for Photoluminescence Quantum Yields.
    """
    specifier = StringType(parse_expression=PLQY_specifier,
                           required=True)
    compound = ModelType(ThemeCompound, contextual=True, required=False, binding=False)
    atmosphere = ModelType(Atmosphere, contextual=False, required=False)
    phase = ModelType(Phase, contextual=False, required=False)
    temperature = ModelType(Temperature, required=False, contextual=False)
    room_temperature = StringType(parse_expression=room_temperature_expression, required=False, contextual=False)
    parsers = [MultiQuantityModelTemplateParser(),
               QuantityModelTemplateParser(),
               DimlessPLQYTableParser(),
               AutoTableParser(),
               ]


# suffix_delayed = (R("^[Dd]elayed\w?$") | R("^(DF)|(TADF)|(df)|(tadf)\w?$") | R("^TADF\w?$")) +\
#          Optional(ZeroOrMore(Any())).hide() + W("%").hide()
# PLQYD_specifier = ((phi + suffix_delayed).add_action(merge) |
#                    (I("delayed") + Optional(I("photoluminescence") + I("quantum")) + I("yield")) |
#                    (I("delayed") + R("^components?$")) |
#                    R("^[ΦφϕⲪⲫɸ𝟇𝞥𝞍𝝫𝝓𝜱𝜙𝛷𝛟𝚽ᶲ]((D|d(elayed)?)|(DF)|(TADF)|(df)|(tadf))$")
#                    )
#

# The following two models were not used in the paper {doi}
# class DelayedQuantumYield(RatioModel, QuantumYield):
#     # TODO: More word specifiers
#     specifier = StringType(parse_expression=PLQYD_specifier,
#                            required=True)
#     compound = ModelType(ThemeCompound, contextual=True, required=True, binding=True)
#     parsers = [MultiQuantityModelTemplateParser(),
#                QuantityModelTemplateParser(),
#                AutoTableParser(),
#                ]
#
#
# suffix_prompt= (R("^[Pp]rompt\w?$") | R("^[Ff]\w?$") | I("fluorescence") | R("^(PF)|(pf)\w?$")) +\
#          Optional(ZeroOrMore(Any())).hide() + W("%").hide()
# PLQYP_specifier = ((phi + suffix_prompt).add_action(merge) |
#                    (I("prompt") | I("fluorescence") + Optional(I("photoluminescence") + I("quantum")) + I("yield")) |
#                    (I("prompt") + R("^components?$")) |
#                    R("^[ΦφϕⲪⲫɸ𝟇𝞥𝞍𝝫𝝓𝜱𝜙𝛷𝛟𝚽ᶲ]((P|p(rompt)?)|(PF)|[Ff]|(pf))$")
#                    )
#
#
# class PromptQuantumYield(RatioModel, QuantumYield):
#     # TODO: More word specifiers
#     specifier = StringType(parse_expression=PLQYP_specifier,
#                            required=True)
#     compound = ModelType(ThemeCompound, contextual=True, required=True, binding=True)
#     parsers = [MultiQuantityModelTemplateParser(),
#                QuantityModelTemplateParser(),
#                AutoTableParser(),
#                ]
