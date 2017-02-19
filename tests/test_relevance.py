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


import numpy as np

from cgpm.mixtures import relevance
from cgpm.mixtures.view import View
from cgpm.utils import general as gu


def test_separated():
    outputs = [1, 2, 3]
    data = np.asarray([
        [0, 0.50, -8.90],
        [0, 0.20, -7.10],
        [1, 1.30, -4.10],
        [1, 1.20, -4.50],
        [1, 1.15, -4.70],
        [0, 1.10, -5.10],
        [2, 2.60, -1.40],
        [1, 2.80, -1.70],
        [3, 8.90, -0.10]
    ])
    assignments = [0, 0, 2, 2, 2, 2, 6, 6, 7]

    view = View(
        outputs=[1000]+outputs,
        X={output: data[:,i] for i, output in enumerate(outputs)},
        alpha=1.5,
        cctypes=['categorical', 'normal', 'normal'],
        distargs=[{'k':4}, None, None],
        Zr=assignments,
        rng=gu.gen_rng(1)
    )

    for i in xrange(10):
        view.transition_dim_hypers()

    # XXX TODO Expand the tests; compuate pairwise, cross-cluster, and
    # multi-cluster relevances.
    assert 0 < np.exp(view.relevance_probability(1, [4,6,7])) < 1
    assert 0 < np.exp(view.relevance_probability(3, [8])) < 1


def test_get_tables_different():
    assert relevance.get_tables_different([0,1]) == (
        [0,1,2], [[1,2], [0,2], [0,1,3]]
    )
    assert relevance.get_tables_different([1,2]) == (
        [1,2,3], [[2,3], [1,3], [1,2,4]]
    )
    assert relevance.get_tables_different([0,4,7,9]) == (
        [0,4,7,9,10],
        [[4,7,9,10], [0,7,9,10], [0,4,9,10], [0,4,7,10], [0,4,7,9,11]]
    )
