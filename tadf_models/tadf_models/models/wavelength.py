from chemdataextractor.parse.elements import I, R, W, Optional, ZeroOrMore, Any, Not, SkipTo
from chemdataextractor.parse.actions import merge
from chemdataextractor.parse import join, AutoTableParser
from chemdataextractor.parse.template import MultiQuantityModelTemplateParser, \
    QuantityModelTemplateParser
from chemdataextractor.model import ModelType, StringType
from chemdataextractor.model.units import LengthModel
from .condition import Phase
from chemdataextractor.model import ThemeCompound

# Define specifiers for emission wavelengths.
lamda = R("^[λ𝛌𝜆𝝀𝝺𝞴]$")
em = R("^[Pp][Ll]\w?$") | R("^[Ee][Mm]\w?$") | R("^[Ee][Ll]\w?$") | R("^[fF][Ll](uo)?\w?$") | R("^[Pp][Hh]o?s?\w?$")
suffix_em = ((em + Optional(R("^[,;]$") + R("^[Mm]ax\w?$"))).add_action(merge) |
             (R("^[Mm]ax\w?$") + R("^[,;]$") + em).add_action(merge) +
                ZeroOrMore(Not(W('nm')) + Any().hide()) + W("nm").hide())

em_word = (I('phosphorescence') | I('fluorescence') | I('electroluminescence') | I('photoluminescence') | W('PL') | W('EL'))

lamda_pl_specifier = ((lamda + suffix_em).add_action(merge) |
                      (R("^[λ𝛌𝜆𝝀𝝺𝞴](([Pp][Ll])|([Ee][Mm])|([Ee][Ll])|([Pp][Hh]o?s?)|([Ff][Ll](uo)?))\w?$") + Optional(R("^[,;]$") + R("^[Mm]ax\w?$"))) |
                      (R("^([λ𝛌𝜆𝝀𝝺𝞴]|(PL)|(EL))[Mm]ax\w?$") + R("^[,;]$") + em) |
                      R("^[λ𝛌𝜆𝝀𝝺𝞴](([Pp][Ll])|([Ee][Mm])|([Ee][Ll])|([Pp][Hh]o?s?)|([Ff][Ll](uo)?))?([Mm]ax)?\w?$") |
                      ((I('emission') | I('emitting') | em_word)
                       + (I('wavelength') | R('^[pP]eaks?(ing)?$') | R('^[Mm]axim[(um)a]$'))) |
                      (em_word +
                       Optional(R('^spectr[(um)a]$') | R('^intensit[(ies)y]')) +
                       SkipTo((R('^peaks?(ed)?$') | R('^cent[(ers?)(res?)]d?$') | W('around') | W("wavelength") | (R('^[Mm]axim[(um)a]$') + Optional(I('wavelength'))))).hide() +
                       (R('^peaks?(ed)?$') | R('^cent[(ers?)(res?)]d?$') | W("wavelength") | W('around') | (R('^[Mm]axim[(um)a]$') + Optional(I('wavelength'))))) |
                      ((I('peak') + R('^wavelengths?$') | R("^positions?$")) + I('of') +
                       (em_word | I('emission')) +
                       R("^spectr[(um)a]$")) |
                      (R('^emit(ted)?(ting)?s?$') +
                       SkipTo((I('peak') | I('maximum')) + R('^wavelengths?$')).hide() +
                       (I('peak') | I('maximum')) + R('^wavelengths?$'))
                      ).add_action(join)


class EmissionWavelength(LengthModel):
    """
    Model for emission wavelengths.
    """
    specifier = StringType(parse_expression=lamda_pl_specifier,
                           required=True)
    compound = ModelType(ThemeCompound, contextual=True, required=False, binding=False)
    phase = ModelType(Phase, contextual=False, required=False, binding=False)
    parsers = [MultiQuantityModelTemplateParser(),
               QuantityModelTemplateParser(),
               AutoTableParser(),
               ]
