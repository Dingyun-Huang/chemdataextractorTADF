import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import torch
import torch.nn as nn
from transformers import AutoModel, PreTrainedModel, AutoConfig, PretrainedConfig, AutoTokenizer
from chemdataextractor.nlp.crf import ConditionalRandomField, allowed_transitions
from chemdataextractor.nlp.allennlp_modules import TimeDistributed
from chemdataextractor.errors import ConfigurationError
from typing import Dict, Optional, List, Tuple
from chemdataextractor.doc import Sentence
from chemdataextractor.data import find_data


class BertCrfConfig(PretrainedConfig):
    model_type = 'bert'
    
    def __init__(
        self,
        num_tags: int = 3,
        dropout=0.1,
        label_namespace: str = "labels",
        label_encoding: Optional[str] = None,
        index_and_label: List[Tuple[int, str]] = None,
        constrain_crf_decoding: bool = True,
        include_start_end_transitions: bool = True,
        model_name_or_path: str = None,
        **kwargs
    ):
        self.num_tags = num_tags
        self.dropout = dropout
        self.label_namespace = label_namespace
        self.label_encoding = label_encoding
        self.index_and_label = index_and_label
        self.constrain_crf_decoding = constrain_crf_decoding
        self.include_start_end_transitions = include_start_end_transitions
        self.model_name_or_path = model_name_or_path
        super().__init__(**kwargs)


class BertCrfTagger(PreTrainedModel):
    config_class = BertCrfConfig  # Required for saving/loading
    
    def __init__(self, config):

        super().__init__(config)
        self.bert_model = AutoModel.from_config(AutoConfig.from_pretrained(config.model_name_or_path))
        self.num_tags = config.num_tags
        self.tag_projection_layer = TimeDistributed(
            nn.Linear(self.bert_model.config.hidden_size, self.num_tags)
        )

        self.label_encoding = config.label_encoding
        self.index_and_label = config.index_and_label
        self.index_to_label = self._index_to_label()
        self.label_to_index = self._label_to_index()
    
        if config.constrain_crf_decoding:
            if not config.label_encoding:
                raise ConfigurationError("constrain_crf_decoding is True, but "
                                         "no label_encoding was specified.")
            labels = self.index_to_label
            constraints = allowed_transitions(config.label_encoding, labels)
        else:
            constraints = None

        self.include_start_end_transitions = config.include_start_end_transitions
        self.crf = ConditionalRandomField(
                self.num_tags, constraints,
                include_start_end_transitions=config.include_start_end_transitions
        )

        
        # Dropout for regularization
        self.dropout = nn.Dropout(config.dropout)
    
    def _index_to_label(self):
        return {index: label for index, label in self.index_and_label}
    
    def _label_to_index(self):
        return {label: index for index, label in self.index_and_label}

    def forward(self, input_ids, attention_mask, labels=None):
        # BERT embeddings
        outputs = self.bert_model(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state
        sequence_output = self.dropout(sequence_output)
        
        # Project onto tag space
        logits = self.tag_projection_layer(sequence_output)
        best_paths = self.crf.viterbi_tags(logits, attention_mask)

        predicted_tags = [x for x, y in best_paths]

        output = {"logits": logits, "mask": attention_mask, "tags": predicted_tags}
        
        return output

    def decode(self, output_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Converts the tag ids to the actual tags.
        ``output_dict["tags"]`` is a list of lists of tag_ids,
        so we use an ugly nested list comprehension.
        """
        output_dict["tags"] = [
                [self.index_to_label[tag]
                 for tag in instance_tags]
                for instance_tags in output_dict["tags"]
        ]
        return output_dict

def main():
    # Load the model
    from tokenizers import BertWordPieceTokenizer
    tagger = BertCrfTagger.from_pretrained(find_data("models/hf_bert_crf_tagger"))
    tokenizer = BertWordPieceTokenizer(vocab=find_data("models/hf_bert_crf_tagger") + '/vocab.txt',) # AutoTokenizer.from_pretrained(find_data("models/hf_bert_crf_tagger"))
    s = "The chemical formula of water is H2O."
    cde_s = Sentence(s)
    cde_tagged_tokens = cde_s.ner_tagged_tokens
    
    _inputs = tokenizer.encode(s)  # tokenizer(s, return_offsets_mapping=True, truncation=False)
    print(_inputs)
    tagger.eval()
    with torch.no_grad():
        output = tagger(torch.tensor([_inputs["input_ids"]]), torch.tensor([_inputs["attention_mask"]]))
        hf_tagger_results = tagger.decode(output)
    
    print(cde_tagged_tokens)
    print(list(zip(tokenizer.convert_ids_to_tokens(_inputs["input_ids"]), hf_tagger_results["tags"][0])))

    
if __name__ == "__main__":
    main()
    