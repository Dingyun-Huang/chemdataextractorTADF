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
from chemdataextractor.nlp.util import combine_initial_dims, uncombine_initial_dims, get_device_of, get_range_vector

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

    def forward(self, input_ids, offsets, crf_mask, token_type_ids=None, labels=None):
        # BERT embeddings
        print(input_ids.size())
        
        if token_type_ids is None:
            token_type_ids = torch.zeros_like(input_ids)

        input_mask = (input_ids != 0).long()

        # input_ids may have extra dimensions, so we reshape down to 2-d
        # before calling the BERT model and then reshape back at the end.
        outputs = self.bert_model(input_ids=combine_initial_dims(input_ids),
                                                token_type_ids=combine_initial_dims(token_type_ids),
                                                attention_mask=combine_initial_dims(input_mask))
        # all_encoder_layers = torch.stack(outputs.last_hidden_state)
        last_hidden_state = outputs.last_hidden_state

        # At this point, mix is (batch_size * d1 * ... * dn, sequence_length, embedding_dim)
        # offsets is (batch_size, d1, ..., dn, orig_sequence_length)
        offsets2d = combine_initial_dims(offsets)
        # now offsets is (batch_size * d1 * ... * dn, orig_sequence_length)
        range_vector = get_range_vector(offsets2d.size(0),
                                                device=get_device_of(last_hidden_state)).unsqueeze(1)
        # selected embeddings is also (batch_size * d1 * ... * dn, orig_sequence_length)
        selected_embeddings = last_hidden_state[range_vector, offsets2d]

        output_embeddings =  uncombine_initial_dims(selected_embeddings, offsets.size())

        # TODO: Sperate the function into two parts: one for the BERT embeddings and the other for the CRF
        sequence_output = self.dropout(output_embeddings)
        print(sequence_output.size())
        # Project onto tag space
        logits = self.tag_projection_layer(sequence_output)
        best_paths = self.crf.viterbi_tags(logits, crf_mask)

        predicted_tags = [x for x, y in best_paths]

        output = {"logits": logits, "mask": crf_mask, "tags": predicted_tags}
        
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
    tagger = BertCrfTagger.from_pretrained(find_data("models/hf_bert_crf_tagger"))
    wordpiece_tokenizer = AutoTokenizer.from_pretrained(find_data("models/hf_bert_crf_tagger"))
    s = "The chemical formula of water is H2O."
    cde_s = Sentence(s)
    tokens = cde_s.tokens
    # cde_tagged_tokens = cde_s.ner_tagged_tokens
    
    text = (token.text
                # if self._do_lowercase and token.text not in self._never_lowercase
                # else token.text
                for token in tokens)
    token_wordpiece_ids = [[wordpiece_tokenizer.convert_tokens_to_ids(wordpiece) for wordpiece in wordpiece_tokenizer.tokenize(token)]
                               for token in text]
    
    offsets = []

    # If we're using initial offsets, we want to start at offset = len(text_tokens)
    # so that the first offset is the index of the first wordpiece of tokens[0].
    # Otherwise, we want to start at len(text_tokens) - 1, so that the "previous"
    # offset is the last wordpiece of "tokens[-1]".
    offset = 1 # len(self._start_piece_ids) - 1

    # Count amount of wordpieces accumulated
    pieces_accumulated = 0
    for token in token_wordpiece_ids:

        # For initial offsets, the current value of ``offset`` is the start of
        # the current wordpiece, so add it to ``offsets`` and then increment it.
        offsets.append(offset)
        offset += len(token)

        pieces_accumulated += len(token)
    
    flat_token_wordpiece_ids = [wordpiece_id for token in token_wordpiece_ids for wordpiece_id in token]
    wordpiece_ids = [wordpiece_tokenizer.cls_token_id] + flat_token_wordpiece_ids + [wordpiece_tokenizer.sep_token_id]
    mask = [1 for _ in offsets]
    
    print("my indexer output:\n", wordpiece_ids)
    print("my offsets:\n", offsets)
    print("my mask:\n", mask)
    tagger.eval()
    with torch.no_grad():
        output = tagger(torch.LongTensor([wordpiece_ids]), torch.LongTensor([offsets]), torch.LongTensor([mask]))
        hf_tagger_results = tagger.decode(output)
    
    # print(cde_tagged_tokens)
    print(list(zip(tokens, hf_tagger_results["tags"][0])))

    
if __name__ == "__main__":
    main()
    