from chemdataextractor.model.units import TemperatureModel
from chemdataextractor.parse.elements import I, R, W, Optional, T, Group, OneOrMore, SkipTo, And, First, Not, Every
from chemdataextractor.parse import join, AutoTableParser, AutoSentenceParser, fix_whitespace
from chemdataextractor.model import StringType
from chemdataextractor.model import BaseModel
from chemdataextractor.parse.cem import solvent_name_options
from chemdataextractor.text import HYPHENS
from chemdataextractor.nlp.tokenize import BertWordTokenizer
import importlib.resources
import re
from chemdataextractor.parse.auto import construct_unit_element, value_element, match_dimensions_of, \
    create_entities_list


class Atmosphere(BaseModel):
    """Model for air or nitrogen environment"""
    atmosphere = StringType(parse_expression=(I('air') | I('nitrogen') | W('N2') | I('argon') | I('inert')), required=True)
    parsers = [AutoTableParser(), AutoSentenceParser()]


# Load the common film material names used in TADF papers/
names = importlib.resources.read_text('tadf_models', 'film_material_names', encoding='utf-8')
names = [line.split(";") for line in names.split('\n')]
film_materials = []
wt = BertWordTokenizer()

# Construct parse phrase for film materials
for name in names:
    for i, n in enumerate(name):
        tokenized_name = wt.tokenize(n)
        parse_ex = []
        for token in tokenized_name:
            # replace all brackets with lbrct and rbrct
            if token in ['(', '[', '{']:
                parse_ex.append(R("^[\(\[\{]$"))
            elif token in [')', ']', '}']:
                parse_ex.append(R("^[\)\]\}]$"))
            # replace all - as T('HYPH')
            elif token in HYPHENS:
                parse_ex.append(T('HYPH'))
            else:
                if i == 0:
                    parse_ex.append(W(token))
                else:
                    parse_ex.append(I(token))
                # if abbrev use W
                # if full use I
        film_materials.append(And(parse_ex).add_action(join).add_action(fix_whitespace))


class Phase(BaseModel):
    """Model for film or solution environment"""
    specifier = StringType(parse_expression=(R("^[Ss]olutions?$") | (Optional(I("thin") + Optional(T("HYPH"))) + R("^[Ff]ilms?$") | R("^[hH]osts?$"))).add_action(join).add_action(fix_whitespace),
                           required=False, contextual=False)
    host = StringType(parse_expression=(solvent_name_options | First(film_materials)), required=False)
    parsers = [AutoTableParser(), AutoSentenceParser()]


class Solvent(BaseModel):
    """Model for solvent"""
    solvent = StringType(parse_expression=solvent_name_options, required=True)
    parsers = [AutoTableParser(), AutoSentenceParser()]


# Define specifier for temperature and room temperature phrases.
temperature_specifier_expression = (I('temperature') | Every([R('^T\w?$'), Not(W("Tg")), Not(W("Td"))]) | I('at') | I('near') | I('around') | I('above'))
room_temperature_expression = (R('^r\.?t\.?$',re.I) | ((I('room')|I('ambient')) + Optional(I('-')) + I('temperature'))).add_action(join)


class TemperatureTableParser(AutoTableParser):
    """ Additions for automated parsing of tables with column containing T = 300K"""

    @property
    def root(self):

        entities = []

        # the special value elements for multientry table column are grouped into a entities list
        # print(self.model, self.model.dimensions)
        unit_element = Group(
            construct_unit_element(self.model.dimensions).with_condition(match_dimensions_of(self.model))(
                'raw_units'))
        specifier = temperature_specifier_expression('specifier')
        value_phrase = (value_element() + unit_element)  # Require that temperature value must be followed by the unit
        entities.append(specifier)
        entities.append(value_phrase)

        # the optional, user-defined, entities of the model are added, they are tagged with the name of the field
        for field in self.model.fields:
            if field not in ['raw_value', 'raw_units', 'value', 'units', 'error', 'specifier']:
                if self.model.__getattribute__(self.model, field).parse_expression is not None:
                    entities.append(self.model.__getattribute__(self.model, field).parse_expression(field))

        # logic for finding all the elements in any order
        combined_entities = create_entities_list(entities)
        root_phrase = OneOrMore(combined_entities + Optional(SkipTo(combined_entities)))('root_phrase')
        return root_phrase


class Temperature(TemperatureModel):
    """Temperature property model"""
    raw_value = StringType(required=True)
    raw_units = StringType(required=True)
    specifier = StringType(parse_expression=temperature_specifier_expression, required=True, contextual=False, updatable=True)
    parsers = [AutoSentenceParser(), TemperatureTableParser()]


class RoomTemperature(BaseModel):
    """Model for room temperature"""
    room_temperature = StringType(parse_expression=room_temperature_expression, required=True)
    parsers = [AutoTableParser(), AutoSentenceParser()]
