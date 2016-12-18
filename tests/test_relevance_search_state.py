# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 MIT Probabilistic Computing Project

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Find the math for these tests in
https://docs.google.com/document/d/15_JGb39TuuSup_0gIBJTuMHYs8HS4m_TzjJ-AOXnh9M/edit
"""

import numpy as np
from itertools import product
from collections import OrderedDict
from pprint import pprint

from cgpm.crosscat.state import State
from cgpm.utils.general import logsumexp, merged


DATA = [[1, 1, 0, 1, 1, 1],
        [1, 1, 1, 0, 1, 1],
        [1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0]]

def initialize_state():
    X = np.array(DATA)
    D = len(X[0])
    outputs = range(D)
    Zv = {c: 0 for c in outputs}
    Zrv = {0: [0 if i < 4 else 1 for i in range(8)]}
    state = State(
        X,
        outputs=outputs,
        alpha=[1.],
        cctypes=['bernoulli']*D,
        hypers={
            i: {'alpha': 1., 'beta': 1.} for i in outputs},
        Zv=Zv,
        Zrv=Zrv)
    return state

def test_relevance_search_wrt_rows_in_first_cluster():
    state = initialize_state()

    for rowid in xrange(4):
        score = state.relevance_search(
            evidence={rowid: {}}, context=0, debug=True)

        # Assert highest score with itself
        assert score[0][0] == rowid

        # Assert highest scoring values come from same cluster as evidence
        first_four = [score[i][0] for i in xrange(4)]
        first_cluster = range(4)
        assert set(first_four) == set(first_cluster)

        # Assert lowest scoring values come from different cluster than evidence
        last_four = [score[i][0] for i in xrange(4, 8)]
        second_cluster = range(4, 8)
        assert set(last_four) == set(second_cluster)

def test_relevance_search_wrt_rows_in_second_cluster():
    state = initialize_state()

    for rowid in xrange(4, 8):
        score = state.relevance_search(
            evidence={rowid: {}}, context=0, debug=True)

        # Assert highest score with itself
        assert score[0][0] == rowid

        # Assert highest scoring values come from same cluster as evidence
        first_four = [score[i][0] for i in xrange(4)]
        second_cluster = range(4, 8)
        assert set(first_four) == set(second_cluster)

        # Assert lowest scoring values come from different cluster than evidence
        last_four = [score[i][0] for i in xrange(4, 8)]
        first_cluster = range(4)
        assert set(last_four) == set(first_cluster)

def test_relevance_search_mixed():
    state = initialize_state()

    score = state.relevance_search(
        evidence={0: {}, 7: {}}, context=0, debug=True)

    # Assert highest scores with itself
    first_two = [score[i][0] for i in xrange(2)]
    assert set(first_two) == {0, 7}

    pprint(score)

def test_relevance_search_wrt_majority():
    state = initialize_state()

    score = state.relevance_search(
        evidence={0: {}, 1: {}, 7: {}}, context=0, debug=True)

    # Assert highest scoring values come from majority cluster in evidence
    first_four = [score[i][0] for i in xrange(4)]
    first_cluster = range(4)
    assert set(first_four) == set(first_cluster)

    # Assert lowest scoring values come from minority cluster in evidence
    last_four = [score[i][0] for i in xrange(4, 8)]
    second_cluster = range(4, 8)
    assert set(last_four) == set(second_cluster)

    pprint(score)