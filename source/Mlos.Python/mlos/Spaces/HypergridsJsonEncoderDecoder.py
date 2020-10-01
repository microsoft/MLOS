#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from json import JSONEncoder, JSONDecoder

from mlos.Spaces import Dimension, EmptyDimension, CategoricalDimension, ContinuousDimension, Point, \
    DiscreteDimension, OrdinalDimension, CompositeDimension, Hypergrid, SimpleHypergrid

class HypergridJsonEncoder(JSONEncoder):

    # pylint: disable=method-hidden
    def default(self, o):
        if isinstance(o, Dimension):
            # TODO: add random state here
            return_dict = dict()

            if isinstance(o, EmptyDimension):
                return_dict["ObjectType"] = "EmptyDimension"
                return_dict["Name"] = o.name
                return_dict["Type"] = o.type.__name__

            elif isinstance(o, ContinuousDimension):
                return_dict["ObjectType"] = "ContinuousDimension"
                return_dict["Name"] = o.name
                return_dict["Min"] = o.min
                return_dict["Max"] = o.max
                return_dict["IncludeMin"] = o.include_min
                return_dict["IncludeMax"] = o.include_max

            elif isinstance(o, DiscreteDimension):
                return_dict["ObjectType"] = "DiscreteDimension"
                return_dict["Name"] = o.name
                return_dict["Min"] = o.min
                return_dict["Max"] = o.max

            elif isinstance(o, OrdinalDimension):
                return_dict["ObjectType"] = "OrdinalDimension"
                return_dict["Name"] = o.name
                return_dict["OrderedValues"] = o.values
                return_dict["Ascending"] = o.ascending

            elif isinstance(o, CategoricalDimension):
                return_dict["ObjectType"] = "CategoricalDimension"
                return_dict["Name"] = o.name
                return_dict["Values"] = o.values

            elif isinstance(o, CompositeDimension):
                return_dict["ObjectType"] = "CompositeDimension"
                return_dict["Name"] = o.name
                return_dict["ChunksType"] = o.chunks_type.__name__
                return_dict["Chunks"] = [chunk for chunk in o.enumerate_chunks()]
            return return_dict

        if isinstance(o, Hypergrid):
            # TODO: serialize random state
            return_dict = dict()
            if isinstance(o, SimpleHypergrid):
                return_dict['ObjectType'] = "SimpleHypergrid"
                return_dict['Name'] = o.name
                return_dict['Dimensions'] = o.root_dimensions
                if o.is_hierarchical():
                    return_dict['GuestSubgrids'] = o.joined_subgrids_by_pivot_dimension
            return return_dict

        if isinstance(o, SimpleHypergrid.JoinedSubgrid):
            return {
                'ObjectType': 'GuestSubgrid',
                'Subgrid': o.subgrid,
                'ExternalPivotDimension': o.join_dimension
            }

        if isinstance(o, Point):
            return o.to_json()

        if isinstance(o, set):
            return {
                "ObjectType": "set",
                "Values": list(o)
            }

        return JSONEncoder.default(self, o)

class HypergridJsonDecoder(JSONDecoder):

    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    # pylint: disable=method-hidden, no-self-use
    def object_hook(self, obj):
        type_names_to_types = {
            "EmptyDimension": EmptyDimension,
            "CategoricalDimension": CategoricalDimension,
            "ContinuousDimension": ContinuousDimension,
            "DiscreteDimension": DiscreteDimension,
            "OrdinalDimension": OrdinalDimension,
            "CompositeDimension": CompositeDimension,
        }

        if 'ObjectType' not in obj:
            return obj

        object_type = obj['ObjectType']

        if object_type == 'EmptyDimension':
            return EmptyDimension(
                name=obj['Name'],
                type=type_names_to_types[obj['Type']]
            )
        if object_type == "CategoricalDimension":
            return CategoricalDimension(
                name=obj['Name'],
                values=obj['Values']
            )
        if object_type == "ContinuousDimension":
            return ContinuousDimension(
                name=obj['Name'],
                min=obj.get('Min', None),
                max=obj.get('Max', None),
                include_min=obj.get('IncludeMin', None),
                include_max=obj.get('IncludeMax', None)
            )
        if object_type == "DiscreteDimension":
            return DiscreteDimension(
                name=obj['Name'],
                min=obj['Min'],
                max=obj['Max']
            )
        if object_type == "OrdinalDimension":
            return OrdinalDimension(
                name=obj['Name'],
                ordered_values=obj.get('OrderedValues', None),
                ascending=obj.get('Ascending', True) # TODO - this looks risky
            )
        if object_type == "CompositeDimension":
            return CompositeDimension(
                name=obj['Name'],
                chunks_type=type_names_to_types[obj['ChunksType']],
                chunks=obj['Chunks']
            )
        if object_type == "SimpleHypergrid":
            simple_hypergrid = SimpleHypergrid(
                name=obj['Name'],
                dimensions=obj.get('Dimensions', [])
            )

            for _, subgrids_joined_on_dimension in obj.get('GuestSubgrids', dict()).items():
                for joined_subgrid in subgrids_joined_on_dimension:
                    simple_hypergrid.add_subgrid_on_external_dimension(
                        other_hypergrid=joined_subgrid.subgrid,
                        external_dimension=joined_subgrid.join_dimension
                    )
            return simple_hypergrid

        if object_type == "GuestSubgrid":
            return SimpleHypergrid.JoinedSubgrid(
                subgrid=obj['Subgrid'],
                join_dimension=obj['ExternalPivotDimension']
            )

        if object_type == "set":
            return set(obj['Values'])

        return obj
