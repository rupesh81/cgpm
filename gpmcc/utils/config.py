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

import re

from gpmcc.dists import normal_uc
from gpmcc.dists import beta_uc
from gpmcc.dists import normal
from gpmcc.dists import binomial
from gpmcc.dists import multinomial
from gpmcc.dists import lognormal
from gpmcc.dists import poisson
from gpmcc.dists import exponential
from gpmcc.dists import exponential_uc
from gpmcc.dists import geometric
from gpmcc.dists import vonmises
from gpmcc.dists import vonmises_uc

dist_class_lookup = {
    'normal'            : normal.Normal,
    'normal_uc'         : normal_uc.NormalUC,
    'beta_uc'           : beta_uc.BetaUC,
    'binomial'          : binomial.Binomial,
    'multinomial'       : multinomial.Multinomial,
    'lognormal'         : lognormal.Lognormal,
    'poisson'           : poisson.Poisson,
    'exponential'       : exponential.Exponential,
    'exponential_uc'    : exponential_uc.ExponentialUC,
    'geometric'         : geometric.Geometric,
    'vonmises'          : vonmises.Vonmises,
    'vonmises_uc'       : vonmises_uc.VonmisesUC,
}

dist_collapsed_lookup = {
        'normal'            : False,
        'normal_uc'         : True,
        'beta_uc'           : True,
        'binomial'          : False,
        'multinomial'       : False,
        'lognormal'         : False,
        'poisson'           : False,
        'exponential'       : False,
        'exponential_uc'    : True,
        'geometric'         : False,
        'vonmises'          : False,
        'vonmises_uc'       : True,
}

def colors():
    """Returns a list of colors for plotting."""
    return ["red", "blue", "green", "yellow", "orange", "purple", "brown",
        "black"]

def is_uncollapsed(dist):
    """Returns a dict of collapsed, uncollapsed column types."""
    return dist_collapsed_lookup[dist]

def dist_class(dist):
    """Return a dict of class objects for initializing distributions."""
    return dist_class_lookup[dist]

def valid_dist(dist):
    """Returns Ture if dist is a valid distribution."""
    return dist in dist_class_lookup

def all_dists():
    """Returns Ture if dist is a valid distribution."""
    return dist_class_lookup.keys()

def parse_distargs(dists):
    """Input ['normal','multinomial(k=8)','beta_uc'].
    Output ['normal','multinomial','beta_uc'], [None, {'k':8}, None].
    """
    disttypes, distargs = [], []
    for dist in dists:
        keywords = re.search('\(.*\)', dist)
        if keywords is not None:
            keywords = keywords.group(0).replace('(','').\
                replace(')','')
            temp = {}
            for subpair in keywords.split(','):
                key, val = subpair.split('=')
                temp[key] = float(val)
            keywords = temp
            dist = dist[:dist.index('(')]
        disttypes.append(dist)
        distargs.append(keywords)
    return disttypes, distargs