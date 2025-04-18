# pylint: disable=line-too-long
"""_summary_
This module contains the implementation of a BERT-CRF tagger for named entity recognition (NER) using the ChemDataExtractor library.
It includes the configuration class `BertCrfConfig`, the tagger class `BertCrfTagger`, and the model class `BertCrfModel`.
The tagger class is responsible for processing and tagging sentences, while the model class defines the BERT-CRF architecture.
Classes:
    BertCrfConfig: Configuration class for the BERT-CRF model.
    BertCrfTagger: Tagger class for named entity recognition using BERT-CRF.
    BertCrfModel: Model class defining the BERT-CRF architecture.
Functions:
    main: Main function to load the model, tokenize a sample sentence, and perform NER tagging.
Usage:
    To use this module, instantiate the `BertCrfTagger` class and call its `tag` or `batch_tag` methods with the input sentences.
    The `main` function provides an example of how to load the model and perform NER tagging on a sample sentence.
"""
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
    s1 = '2-(4-Chloro-2-fluoro-3-difluoromethylphenyl)-[1,3,2]-dioxaborinane 1H NMR (CDCl3):'
    
    hf_cde_s1 = Sentence(s1)
    hf_cde_tagged_tokens = hf_cde_s1.ner_tagged_tokens
    print("HF tagged tokens", hf_cde_tagged_tokens)


if __name__ == "__main__":
    main()
