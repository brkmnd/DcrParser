#!/usr/bin/env python3
# conding=utf-8
#
# Copyright 2020 Institute of Formal and Applied Linguistics, Faculty of
# Mathematics and Physics, Charles University, Czech Republic.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from model.head.abstract_head import AbstractHead
from data.parser.to_mrp.dcr_parser import DcrParser
from utility.hungarian_matching import get_matching, reorder, match_smoothed_label, match_anchor


class DcrHead(AbstractHead):
    def __init__(self, dataset, args, framework, language, initialize: bool):
        config = {
            "label": True,
            "property": False,
            "top": True,
            "edge presence": True,
            "edge label": True,
            "edge attribute": False,
            "anchor": True
        }
        super(DcrHead, self).__init__(dataset, args, framework, language, config, initialize)
        self.parser = DcrParser(dataset, language)

