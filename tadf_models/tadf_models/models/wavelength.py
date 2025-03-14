from chemdataextractor.parse.elements import (
    I,
    R,
    W,
    Optional,
    ZeroOrMore,
    Any,
    Not,
    SkipTo,
)
from chemdataextractor.parse.actions import merge
from chemdataextractor.parse import join, AutoTableParser
from chemdataextractor.parse.template import (
    MultiQuantityModelTemplateParser,
    QuantityModelTemplateParser,
)
from chemdataextractor.model import ModelType, StringType
from chemdataextractor.model.units import LengthModel
from .condition import Phase
from chemdataextractor.model import ThemeCompound
from .condition import Temperature, RoomTemperature, Solvent
from chemdataextractor.model.contextual_range import (
    SentenceRange,
    ParagraphRange,
)

# Define specifiers for emission wavelengths.
lamda = R("^[λ𝛌𝜆𝝀𝝺𝞴]$")
pl = R("^[Pp][Ll]\w?$")  # photo luminescence
fl = R("^[Ff][Ll](uo)?\w?$")  # fluorescence
el = R("^[Ee][Ll]\w?$")  # electroluminescence
ph = R("^[Pp][Hh]o?s?\w?$")  # phosphorescence
em = R("^[Ee][Mm]\w?$") | pl | fl | el | ph  # general emission
suffix_em = (em + Optional(R("^[,;]$") + R("^[Mm]ax\w?$"))).add_action(merge) | (
    R("^[Mm]ax\w?$") + R("^[,;]$") + em
).add_action(merge) + ZeroOrMore(Not(W("nm")) + Any().hide()) + W("nm").hide()

em_word = (
    I("phosphorescence")
    | I("fluorescence")
    | I("electroluminescence")
    | I("photoluminescence")
    | W("PL")
    | W("EL")
)

# specifier for all emission wavelengths
lamda_em_specifier = (
    (lamda + suffix_em).add_action(merge)
    | (
        R(
            "^[λ𝛌𝜆𝝀𝝺𝞴](([Pp][Ll])|([Ee][Mm])|([Ee][Ll])|([Pp][Hh]o?s?)|([Ff][Ll](uo)?))\w?$"
        )
        + Optional(R("^[,;]$") + R("^[Mm]ax\w?$"))
    )
    | (R("^([λ𝛌𝜆𝝀𝝺𝞴]|(PL)|(EL))[Mm]ax\w?$") + R("^[,;]$") + em)
    | R(
        "^[λ𝛌𝜆𝝀𝝺𝞴](([Pp][Ll])|([Ee][Mm])|([Ee][Ll])|([Pp][Hh]o?s?)|([Ff][Ll](uo)?))?([Mm]ax)?\w?$"
    )
    | (
        (I("emission") | I("emitting") | em_word)
        + (I("wavelength") | R("^[pP]eaks?(ing)?$") | R("^[Mm]axim[(um)a]$"))
    )
    | (
        em_word
        + Optional(R("^spectr[(um)a]$") | R("^intensit[(ies)y]"))
        + SkipTo(
            (
                R("^peaks?(ed)?$")
                | R("^cent[(ers?)(res?)]d?$")
                | W("around")
                | W("wavelength")
                | (R("^[Mm]axim[(um)a]$") + Optional(I("wavelength")))
            )
        ).hide()
        + (
            R("^peaks?(ed)?$")
            | R("^cent[(ers?)(res?)]d?$")
            | W("wavelength")
            | W("around")
            | (R("^[Mm]axim[(um)a]$") + Optional(I("wavelength")))
        )
    )
    | (
        (I("peak") + R("^wavelengths?$") | R("^positions?$"))
        + I("of")
        + (em_word | I("emission"))
        + R("^spectr[(um)a]$")
    )
    | (
        R("^emit(ted)?(ting)?s?$")
        + SkipTo((I("peak") | I("maximum")) + R("^wavelengths?$")).hide()
        + (I("peak") | I("maximum"))
        + R("^wavelengths?$")
    )
).add_action(join)


# specifiers for tadf photoluminescence wavelength (also fluorescence)
# TODO: Should I include EM keywords in the specifier? Currently, it is included for a first test.

pl = R("^[Ee][Mm]\w?$") | pl | fl
suffix_pl = (pl + Optional(R("^[,;]$") + R("^[Mm]ax\w?$"))).add_action(merge) | (
    R("^[Mm]ax\w?$") + R("^[,;]$") + pl
).add_action(merge) + ZeroOrMore(Not(W("nm")) + Any().hide()) + W("nm").hide()
tadf_pl_word = I("photoluminescence") | W("PL") | I("fluorescence") | I("emission")

lamda_pl_specifier = (
    W("PL")
    | (lamda + suffix_pl).add_action(merge)
    | (
        R(r"^[λ𝛌𝜆𝝀𝝺𝞴](([Pp][Ll])|([Ee][Mm])|([Ff][Ll](uo)?))\w?$")
        + Optional(R("^[,;]$") + R(r"^[Mm]ax\w?$"))
    ).add_action(
        merge
    )  # done
    | (R(r"^[λ𝛌𝜆𝝀𝝺𝞴][Mm]ax\w?$") + R("^[,;]$") + pl).add_action(merge)
    | (R(r"^PL[Mm]ax\w?$"))
    | R(r"^[λ𝛌𝜆𝝀𝝺𝞴](([Pp][Ll])|([Ee][Mm])|([Ff][Ll](uo)?))\w?$")
    # | (R(r"^[λ𝛌𝜆𝝀𝝺𝞴][Mm]ax\w?$"))
    | (
        (I("emission") | I("emitting") | tadf_pl_word)  # done
        + (I("wavelength") | R(r"^[pP]eaks?(ing)?$") | R(r"^[Mm]axim[(um)a]$"))
    ).add_action(
        join
    )  # done
    | (
        tadf_pl_word  # done
        + Optional(R(r"^spectr[(um)a]$") | R(r"^intensit[(ies)y]"))
        + SkipTo(
            (
                R(r"^peaks?(ed)?$")
                | R(r"^cent[(ers?)(res?)]d?$")
                | W("around")
                | W("wavelength")
                | (R(r"^[Mm]axim[(um)a]$") + Optional(I("wavelength")))
            )
        ).hide()
        + (
            R(r"^peaks?(ed)?$")
            | R(r"^cent[(ers?)(res?)]d?$")
            | W("wavelength")
            | W("around")
            | (R(r"^[Mm]axim[(um)a]$") + Optional(I("wavelength")))
        )
    ).add_action(
        join
    )  # done
    | (
        (I("peak") + R(r"^wavelengths?$") | R(r"^positions?$"))
        + I("of")
        + (tadf_pl_word | I("emission"))
        + R(r"^spectr[(um)a]$")
    ).add_action(
        join
    )  # done
    | (
        R(r"^emit(ted)?(ting)?s?$")
        + SkipTo((I("peak") | I("maximum")) + R(r"^wavelengths?$")).hide()
        + (I("peak") | I("maximum"))
        + R(r"^wavelengths?$")
    ).add_action(
        join
    )  # done
)


class PhotoluminescenceWavelength(LengthModel):
    """
    Model for photoluminescence wavelengths.
    """

    context = ""
    specifier = StringType(parse_expression=lamda_pl_specifier, required=True)
    compound = ModelType(
        ThemeCompound,
        contextual=True,
        required=True,
        binding=False,
        contextual_range=1 * SentenceRange(),
    )
    solvent = ModelType(
        Solvent, required=False, contextual=True, contextual_range=1 * SentenceRange()
    )
    temperature = ModelType(
        Temperature,
        required=False,
        contextual=True,
        contextual_range=1 * SentenceRange(),
    )
    room_temperature = ModelType(
        RoomTemperature,
        required=False,
        contextual=True,
        contextual_range=1 * SentenceRange(),
    )
    parsers = [
        # MultiQuantityModelTemplateParser(),
        # QuantityModelTemplateParser(),
        AutoTableParser(),
    ]


class EmissionWavelength(LengthModel):
    """
    Model for emission wavelengths.
    """

    specifier = StringType(parse_expression=lamda_em_specifier, required=True)
    compound = ModelType(ThemeCompound, contextual=True, required=False, binding=False)
    phase = ModelType(Phase, contextual=False, required=False, binding=False)
    parsers = [
        MultiQuantityModelTemplateParser(),
        QuantityModelTemplateParser(),
        AutoTableParser(),
    ]
