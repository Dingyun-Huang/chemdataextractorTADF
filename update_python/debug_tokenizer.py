import copy
import datetime
import logging
import warnings
import math
from typing import Dict, List, Optional, Tuple

warnings.simplefilter(action='ignore', category=FutureWarning)

import torch
import torch.nn as nn
import numpy as np
from transformers import (AutoConfig, AutoModel, AutoTokenizer, DefaultDataCollator,
                          PretrainedConfig, PreTrainedModel)
from yaspin import yaspin

from chemdataextractor.data import find_data
from chemdataextractor.doc import Sentence, Document
from chemdataextractor.errors import ConfigurationError
from chemdataextractor.nlp.allennlp_modules import TimeDistributed
from chemdataextractor.nlp.crf import (ConditionalRandomField,
                                       allowed_transitions)
from chemdataextractor.nlp.tag import BaseTagger, NER_TAG_TYPE
from chemdataextractor.nlp.util import (combine_initial_dims, get_device_of,
                                        get_range_vector,
                                        uncombine_initial_dims)
from chemdataextractor.nlp.hf_replaced_tagger import BertCrfTagger
from chemdataextractor.nlp.new_cem import BertFinetunedCRFCemTagger

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)




def main():
    # Load the model
    # model = BertCrfModel.from_pretrained(
    #     find_data("models/hf_bert_crf_tagger"))
    # wordpiece_tokenizer = AutoTokenizer.from_pretrained(
    #     find_data("models/hf_bert_crf_tagger"))
    s = '2-(4-Chloro-2-fluoro-3-difluoromethylphenyl)-[1,3,2]-dioxaborinane 1H NMR (CDCl3):'
    
    test_s = Sentence(s)
    hf_cde_tagged_tokens = test_s.ner_tagged_tokens


if __name__ == '__main__':
    main()
