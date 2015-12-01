# -*- coding: utf-8 -*-

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import multiprocessing

import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import logsumexp

from gpmcc.utils import test as tu
from gpmcc.utils import general as gu
from particle_dim import ParticleDim

def logmeanexp(values):
    return logsumexp(values) - np.log(len(values))

# Fix seed for random dataset.
np.random.seed(10)

# set up the data generation
n_rows = 15
view_weights = np.ones(1)
cluster_weights = [np.asarray([.5, .3, .2])]
dists = ['normal']
separation = [.8]
distargs = [None]
T, Zv, Zc,= tu.gen_data_table(n_rows, view_weights, cluster_weights, dists,
    distargs, separation)

# num_particles = 1
# dims = []
# for i in xrange(num_particles):
#     dims.append(ParticleDim('normal'))
#     dims[-1].particle_learn(T[0], progress=True)

dim = ParticleDim('normal_uc')
dim.particle_learn(T[0], progress=True)

# Test against synthetic data.
# for t in T[0]:
#     observe_data(t)