#!/usr/bin/env python3
# conding=utf-8
#
# Copyright 2020 Institute of Formal and Applied Linguistics, Faculty of
# Mathematics and Physics, Charles University, Czech Republic.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from data.parser.to_mrp.abstract_parser import AbstractParser

class DcrParser(AbstractParser):
    def __init__(self, dataset, language):
        super().__init__(dataset, language)

    def parse(self, prediction):
        output = {}

        output["id"] = self.dataset.id_field.vocab.itos[prediction["id"].item()]
        output["nodes"] = self.create_nodes(prediction)
        output["nodes"] = self.create_anchors(prediction, output["nodes"])
        #output["nodes"] = self.create_properties(prediction, output["nodes"])
        output["edges"] = self.create_edges(prediction, output["nodes"])
        output["tops"] = self.create_top(prediction, output["nodes"])

        return output

    def label_to_str(self, label, anchors, prediction):
        threshold = min(0.0, anchors.max().item())
        label = self.dataset.relative_output_tensor_to_str(
            label - 1,
            (anchors >= threshold).nonzero(as_tuple=False).squeeze(-1),
            prediction["tokens"],
            prediction["lemmas"],
            concat_rules=True,
        )
        label = label.replace('/', '\\/')
        return label
    
    """
    def create_top(self, prediction, nodes):
        for i, node in enumerate(nodes):
            if "label" not in node:
                return [i]
        return [0]
    """

"""
class DcrParser(AbstractParser):
    def parse(self, prediction):
        output = {}

        output["id"] = self.dataset.id_field.vocab.itos[prediction["id"].item()]
        output["nodes"] = self.create_nodes(prediction)
        output["nodes"] = self.create_anchors(prediction, output["nodes"], at_least_one=False)
        #output["nodes"] = self.create_properties(prediction, output["nodes"])
        output["edges"] = self.create_edges(prediction, output["nodes"])
        output["tops"] = self.create_top(prediction, output["nodes"])

        return output

    def label_to_str(self, label, anchors, prediction):
        return self.dataset.relative_output_tensor_to_str(
            label - 1,
            anchors,
            prediction["tokens"],
            prediction["lemmas"],
            concat_rules=False,
        )
"""
