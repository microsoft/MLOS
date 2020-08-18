import json
import os
import sys

mlos_root_path = os.environ['MLOS_ROOT']
mlos_python_root_path = os.path.join(mlos_root_path, 'Source', 'Mlos.Python')
sys.path.append(mlos_python_root_path)

from mlos.Spaces import SimpleHypergrid, EmptyDimension, CategoricalDimension, ContinuousDimension, DiscreteDimension, OrdinalDimension
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonEncoder, HypergridJsonDecoder

continuous = ContinuousDimension(name='continuous', min=1, max=10)
discrete = DiscreteDimension(name='discrete', min=1, max=10)
ordinal = OrdinalDimension(name='ordinal', ordered_values=[1,2,3,4,5,6,7,8,9,10])
categorical = CategoricalDimension(name='categorical', values=[1,2,3,4,5,6,7,8,9,10])

simple_hypergrid = SimpleHypergrid(
    name='all_kinds_of_dimensions',
    dimensions = [
        continuous,
        discrete,
        ordinal,
        categorical
    ]
)

py_simple_hypergrid_json_string = json.dumps(simple_hypergrid, cls=HypergridJsonEncoder)
