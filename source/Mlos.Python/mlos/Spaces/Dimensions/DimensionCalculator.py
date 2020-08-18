#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
The problem with Object-Oriented approach to operators on the various Dimension types was that it introduced
    circular dependencies: a ContinuousDimension needed to know how to interact with a DiscreteDimension and the
    DiscreteDimension needed to know how to interact with a ContinuousDimension. This in turned forced all the
    dimension sub-types to live in a single file and made it difficult to navigate and understand the Dimension type
    system.



What we really need to do is provide implementations for a lot of different
operators.

Here are all the Dimension types:
1) EmptyDimension
2) ContinuousDimension
3) DiscreteDimension
4) OrdinalDimension
5) CategoricalDimension
6) CompositeDimension

In theory all types could interact with all others giving rise to 6 x 6 = 36
different overloads for each of the following operators:
* intersects
* contains
* intersection
* union
* difference

That in turn would yield 36 * 5 = 180 various overloads. This is a lot of code.

Fortunately, many will be trivial or not allowed. For now we can prohibit
heterogeneous interactions between Continuous, Discrete, Ordinal, and Categorical,
and the EmptyDimension will have a trivial implementation for most of its operators.

In any case, it doesn't make sense to encapsulate these methods in a class.
To avoid the circular dependency problem, we'll monkey patch the *Dimension classes
and this works well with unbound functions.
"""

from functools import wraps

from .CategoricalDimension import CategoricalDimension
from .CompositeDimension import CompositeDimension, get_next_chunk
from .ContinuousDimension import ContinuousDimension
from .DiscreteDimension import DiscreteDimension
from .EmptyDimension import EmptyDimension
from .OrdinalDimension import OrdinalDimension


def assert_argument_types(type1, type2):
    """ Asserts that the first two arguments are of given types.

    Sometimes Python needs a little help.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if len(args) != 2:
                raise RuntimeError(f"{f.__qualname__} should take exactly 2 arguments. Not {len(args)}")
            if not isinstance(args[0], type1):
                raise TypeError(f"First argument to {f.__qualname__} should be of type {type1} not {type(args[0])}")
            if not isinstance(args[1], type2):
                raise TypeError(f"Second argument to {f.__qualname__} should be of type {type2} not {type(args[1])}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


###########################################################################


###########################################################################
#
#                                   Intersection
#
###########################################################################


def continuous_intersection_continuous(original, other):
    return original.intersection_continuous_dimension(other)


def composite_intersection_continuous(composite, continuous):
    assert composite.chunks_type is ContinuousDimension
    overlapping_chunks = composite.pop_overlapping_chunks(continuous)
    if not overlapping_chunks:
        return EmptyDimension(name=composite.name, type=composite.chunks_type)
    if len(overlapping_chunks) == 1:
        return overlapping_chunks[0].intersection_continuous_dimension(continuous)
    return CompositeDimension(
        name=composite.name,
        chunks_type=composite.chunks_type,
        chunks=[chunk.intersection(continuous) for chunk in overlapping_chunks]
    )


def composite_intersection_discrete(composite, discrete):
    assert composite.chunks_type is DiscreteDimension
    overlapping_chunks = composite.pop_overlapping_chunks(discrete)
    if not overlapping_chunks:
        return EmptyDimension(name=composite.name, type=composite.chunks_type)
    if len(overlapping_chunks) == 1:
        return overlapping_chunks[0].intersection_discrete_dimension(discrete)
    return CompositeDimension(
        name=composite.name,
        chunks_type=composite.chunks_type,
        chunks=[chunk.intersection(discrete) for chunk in overlapping_chunks]
    )


def continuous_intersection_composite(continuous, composite):
    return composite_intersection_continuous(composite, continuous)


def any_intersection_empty(original, empty):
    assert original.name == empty.name
    assert isinstance(original, empty.type)
    return empty.copy()


def discrete_intersection_discrete(original, other):
    return original.intersection_discrete_dimension(other)


def discrete_intersection_composite(original, other):
    overlapping_chunks = other.pop_overlapping_chunks(original)
    if not overlapping_chunks:
        return EmptyDimension(name=original.name, type=DiscreteDimension)

    if len(overlapping_chunks) == 1:
        return original.intersection(overlapping_chunks[0])

    # We have multiple chunks that intersect
    intersection_chunks = [
        original.intersection(chunk)
        for chunk
        in overlapping_chunks
    ]

    return CompositeDimension(
        name=original.name,
        chunks_type=DiscreteDimension,
        chunks=intersection_chunks
    )


def ordinal_intersection_ordinal(original, other):
    return original.intersection_ordinal_dimension(other)


def categorical_intersection_categorical(original, other):
    return original.intersection_categorical_dimension(other)


def composite_intersection_composite(original, other):
    intersection_chunks = []
    # TODO: how much does the nesting order matter here?
    for chunk in original.enumerate_chunks():
        for overlapping_chunk in other.pop_overlapping_chunks():
            intersection_chunks.append(chunk.intersection(overlapping_chunk))

    if not intersection_chunks:
        return EmptyDimension(name=original.name, type=original.chunks_type)

    if len(intersection_chunks) == 1:
        return intersection_chunks[0].copy()

    return CompositeDimension(
        name=original.name,
        chunks_type=original.chunks_type,
        chunks=intersection_chunks
    )


def empty_intersection_any(original, other):
    assert original.name == other.name
    assert isinstance(other, original.type)
    return original.copy()


# INTERSECTION IMPLEMENTATIONS
intersection_implementations = {
    (ContinuousDimension, ContinuousDimension): continuous_intersection_continuous,
    (ContinuousDimension, CompositeDimension): continuous_intersection_composite,
    (ContinuousDimension, EmptyDimension): any_intersection_empty,
    (DiscreteDimension, DiscreteDimension): discrete_intersection_discrete,
    (DiscreteDimension, CompositeDimension): discrete_intersection_composite,
    (DiscreteDimension, EmptyDimension): any_intersection_empty,
    (OrdinalDimension, OrdinalDimension): ordinal_intersection_ordinal,
    (OrdinalDimension, EmptyDimension): any_intersection_empty,
    (CategoricalDimension, CategoricalDimension): categorical_intersection_categorical,
    (CategoricalDimension, EmptyDimension): any_intersection_empty,
    (CompositeDimension, ContinuousDimension): composite_intersection_continuous,
    (CompositeDimension, DiscreteDimension): composite_intersection_discrete,
    (CompositeDimension, CompositeDimension): composite_intersection_composite,
    (CompositeDimension, EmptyDimension): any_intersection_empty,
    (EmptyDimension, ContinuousDimension): empty_intersection_any,
    (EmptyDimension, DiscreteDimension): empty_intersection_any,
    (EmptyDimension, OrdinalDimension): empty_intersection_any,
    (EmptyDimension, CategoricalDimension): empty_intersection_any,
    (EmptyDimension, CompositeDimension): empty_intersection_any,
    (EmptyDimension, EmptyDimension): empty_intersection_any,
}


def assert_type_compatibility(original, other):
    if isinstance(original, CompositeDimension):
        if isinstance(other, CompositeDimension):
            assert original.chunks_type == other.chunks_type
        else:
            assert original.chunks_type == type(other)

    elif isinstance(other, CompositeDimension):
        assert other.chunks_type == type(original)

def universal_intersection_implementation(original, other):
    assert original.name == other.name
    assert_type_compatibility(original, other)

    specific_intersection_implementation = intersection_implementations.get((type(original), type(other)), None)
    if specific_intersection_implementation is None:
        raise TypeError(
            f"The intersection operation is not supported for operands: "
            f"dimension {original.name} of type: {type(original)}, and "
            f"dimension {other.name} of type: {type(other)}."
        )
    return specific_intersection_implementation(original, other)


# DIFFERENCE IMPLEMENTATIONS
def any_difference_empty(original, _):
    return original.copy()


def empty_difference_any(original, _):
    return original.copy()


def continuous_difference_continuous(original, other):
    intersection = original.intersection(other)

    if isinstance(intersection, EmptyDimension):
        return original.copy()
    if intersection == original:
        return original.make_empty()

    left, right = original.split_on(other)

    if isinstance(left, EmptyDimension):
        return right
    if isinstance(right, EmptyDimension):
        return left

    return CompositeDimension(name=original.name, chunks_type=ContinuousDimension, chunks=[left, right])


def continuous_difference_composite(original, other):
    intersection = original.intersection(other)

    if isinstance(intersection, EmptyDimension):
        return original.copy()

    if isinstance(intersection, ContinuousDimension):
        return continuous_difference_continuous(original, intersection)

    if isinstance(intersection, CompositeDimension):
        original = CompositeDimension(name=original.name, chunks_type=CompositeDimension, chunks=original)
        return composite_difference_composite(original, intersection)

    raise RuntimeError(f"Intersection shuold be one of: EmptyDimension, ContinuousDimension, CompositeDimension. Not: type(intersection)")


def discrete_difference_discrete(original, other):
    intersection = original.intersection(other)

    if isinstance(intersection, EmptyDimension):
        return original.copy()

    if intersection == original:
        return original.make_empty()

    left, _ = original.split_on(intersection.min)
    _, right = original.split_on(intersection.max)

    if isinstance(left, EmptyDimension):
        return right
    if isinstance(right, EmptyDimension):
        return left

    return CompositeDimension(name=original.name, chunks_type=DiscreteDimension, chunks=[left, right])


def discrete_difference_composite(original, other):
    intersection = original.intersection(other)
    assert isinstance(intersection, (EmptyDimension, DiscreteDimension, CompositeDimension))

    if isinstance(intersection, EmptyDimension):
        return original.copy()

    if isinstance(intersection, DiscreteDimension):
        return discrete_difference_discrete(original, intersection)

    if isinstance(intersection, CompositeDimension):
        result = CompositeDimension(
            name=original.name,
            chunks_type=DiscreteDimension,
            chunks=[original]
        )
        return composite_difference_composite(result, intersection)

    raise RuntimeError(f"Intersection shuold be one of: EmptyDimension, ContinuousDimension, CompositeDimension. Not: type(intersection)")

def ordinal_difference_ordinal(original, other):
    return original.difference_ordinal_dimension(other)


def categorical_difference_categorical(original, other):
    return original.difference_categorical_dimension(other)


def composite_difference_continuous(original, other):
    result = original.copy()
    overlapping_chunks = result.pop_overlapping_chunks(other)

    for chunk in overlapping_chunks:
        left, right = chunk.split_on(other)
        if not isinstance(left, EmptyDimension):
            result.push(left)
        if not isinstance(right, EmptyDimension):
            result.push(right)
    return result


def composite_difference_discrete(composite, discrete):
    result = composite.copy()
    overlapping_chunks = result.pop_overlapping_chunks(discrete)

    for chunk in overlapping_chunks:
        left, _ = chunk.split_on(discrete.min)
        _, right = chunk.split_on(discrete.max)
        if not isinstance(left, EmptyDimension):
            result.push(left)
        if not isinstance(right, EmptyDimension):
            result.push(right)
    return result

def composite_difference_composite(original, other):
    """ Subtract all elements that belong to other from original.

    This is a tricky one, as we have to subtract one tree from another.
    Good thing we can iterate over both trees in linear time and perform the entire difference operation
    in linear time as well.

    We will maintain two chunks: original_chunk and other_chunk. We will use the iterators for both
    original and other to get the next chunk whenever the current chunk falls completely behind its counterpart.
    """
    original_chunks_enumerator = original.enumerate_chunks
    other_chunks_enumerator = other.enumerate_chunks

    result = CompositeDimension(
        name=original.name,
        chunks_type=original.chunks_type
    )

    original_chunk = get_next_chunk(original_chunks_enumerator)
    other_chunk = get_next_chunk(other_chunks_enumerator)

    while original_chunk is not None:
        if other_chunk is None or original_chunk.precedes(other_chunk):
            # we are in luck - that entire chunk goes into result
            result.push(original_chunk)
            original_chunk = get_next_chunk(original_chunks_enumerator)
            continue

        if other_chunk.precedes(original_chunk):
            # we are also in luck - the other chunks haven't caught up yet
            other_chunk = get_next_chunk(other_chunks_enumerator)
            continue

        # Not so much luck - they overlap
        # The tricky part is that N consecutive other_chunks could split original_chunk into (up to N+1) sub-chunks
        # In other words, we should advance other_chunks until they are fully beyond original chunk,
        left, right = original_chunk.split_on(other_chunk)
        if not isinstance(left, EmptyDimension):
            result.push(left)

        if not isinstance(right, EmptyDimension):
            # Here, we have a portion of the original_chunk that was larger than the other_chunk.
            # instead of pushing it, let's turn it into original chunk
            original_chunk = right
            other_chunk = get_next_chunk(other_chunks_enumerator)
            continue

    return result

difference_implementations = {
    (ContinuousDimension, ContinuousDimension): continuous_difference_continuous,
    (ContinuousDimension, CompositeDimension): continuous_difference_composite,
    (ContinuousDimension, EmptyDimension): any_difference_empty,
    (DiscreteDimension, DiscreteDimension): discrete_difference_discrete,
    (DiscreteDimension, CompositeDimension): discrete_difference_composite,
    (DiscreteDimension, EmptyDimension): any_difference_empty,
    (OrdinalDimension, OrdinalDimension): ordinal_difference_ordinal,
    (OrdinalDimension, EmptyDimension): any_difference_empty,
    (CategoricalDimension, CategoricalDimension): categorical_difference_categorical,
    (CategoricalDimension, EmptyDimension): any_difference_empty,
    (CompositeDimension, ContinuousDimension): composite_difference_continuous,
    (CompositeDimension, DiscreteDimension): composite_difference_discrete,
    (CompositeDimension, CompositeDimension): composite_difference_composite,
    (CompositeDimension, EmptyDimension): any_difference_empty,
    (EmptyDimension, ContinuousDimension): empty_difference_any,
    (EmptyDimension, DiscreteDimension): empty_difference_any,
    (EmptyDimension, OrdinalDimension): empty_difference_any,
    (EmptyDimension, CategoricalDimension): empty_difference_any,
    (EmptyDimension, CompositeDimension): empty_difference_any,
    (EmptyDimension, EmptyDimension): empty_difference_any,
}


def universal_difference_implementation(original, other):
    assert original.name == other.name
    assert_type_compatibility(original, other)

    specific_difference_implementation = difference_implementations.get((type(original), type(other)), None)
    if specific_difference_implementation is None:
        raise TypeError(
            f"The difference operation is not supported for operands: "
            f"dimension {original.name} of type: {type(original)}, and "
            f"dimension {other.name} of type: {type(other)}."
        )
    return specific_difference_implementation(original, other)


# UNION IMPLEMENTATIONS
def continuous_union_continuous(original, other):
    if original.intersects(other) or original.is_contiguous_with(other):
        return original.union_overlapping_continuous_dimension(other)
    return CompositeDimension(
        name=original.name,
        chunks_type=ContinuousDimension,
        chunks=[original, other]
    )


def continuous_union_composite(original, other):
    return composite_union_continuous(other, original)


def any_union_empty(original, _):
    return original.copy()


def discrete_union_discrete(original, other):
    if original.intersects(other) or original.is_contiguous_with(other):
        return original.union_contiguous_discrete_dimension(other)
    return CompositeDimension(
        name=original.name,
        chunks_type=DiscreteDimension,
        chunks=[original, other]
    )


def discrete_union_composite(original, other):
    return composite_union_discrete(other, original)


def ordinal_union_ordinal(original, other):
    return original.union_ordinal_dimension(other)


def categorical_union_categorical(original, other):
    return original.union_categorical_dimension(other)


def composite_union_continuous(original, other):
    result = original.copy()
    overlapping_chunks = result.pop_overlapping_chunks(other)
    adjacent_chunks = result.pop_adjacent_chunks(other)

    overlapping_chunks.extend(adjacent_chunks)

    if not overlapping_chunks:
        result.push(other)
    else:
        # If there are overlapping chunks, at the end of the day they will all
        # be combined into one. Which means we only need to grab the smallest and the
        # largest and union with those.

        overlapping_chunks = sorted(overlapping_chunks, key=lambda chunk: chunk.min)
        result.push(other.union(overlapping_chunks[0]).union(overlapping_chunks[-1]))
    return result



def composite_union_discrete(original, other):
    """ Unions a composite dimension with a discrete one.

    Now that we only allow the stride inside a discrete dimension to be 1, we turned the problem
    from hard to easy. It is now implemented almost exactly as composite_union_continuous.

    """
    result = original.copy()
    overlapping_chunks = result.pop_overlapping_chunks(other)
    adjacent_chunks = result.pop_adjacent_chunks(other)

    overlapping_chunks.extend(adjacent_chunks)

    if not overlapping_chunks:
        result.push(other)
    else:
        # If there are overlapping chunks, at the end of the day they will all
        # be combined into one. Which means we only need to grab the smallest and the
        # largest and union with those.

        overlapping_chunks = sorted(overlapping_chunks, key=lambda chunk: chunk.min)
        result.push(other.union(overlapping_chunks[0]).union(overlapping_chunks[-1]))
    return result


def composite_union_composite(original, other):
    """ Unions two composite dimensions.

    The algorithm is basically the same as with the difference. We iterate over sorted chunks
    in both dimensions union-ing ones that overlap (or are contiguous). Once we encounter a
    discontinuity we push the accumulated chunk into the resulting CompositeDimension and
    start the accumulation process from the next chunk.

    """
    original_chunks_enumerator = original.enumerate_chunks
    other_chunks_enumerator = other.enumerate_chunks

    result = CompositeDimension(
        name=original.name,
        chunks_type=original.chunks_type
    )

    original_chunk = get_next_chunk(original_chunks_enumerator)
    other_chunk = get_next_chunk(other_chunks_enumerator)

    while original_chunk is not None:
        if other_chunk is None or original_chunk.precedes(other_chunk):
            # Simple case - no overlap so just push the original chunk.
            result.push(original_chunk)
            original_chunk = get_next_chunk(original_chunks_enumerator)
            continue

        if other_chunk.precedes(original_chunk):
            # Simple case - no overlap so just push the other chunk.
            result.push(other_chunk)
            other_chunk = get_next_chunk(other_chunks_enumerator)
            continue

        # If neither precedes the other, means they overlap. Let's make sure.
        assert original_chunk.intersects(other_chunk) # TODO: remove for perf reasons maybe

        # We can't simply push the union into result because we could have a "zipper-like"
        # pattern. We need to accumulate until we encounter a discontinuity.
        # We know that the within a single CompositeDimension are discontinuous (no two chunks
        # overlap) so we know that we need to only advance the smaller of the two.

        accumulated_union = original_chunk.union(other_chunk)

        if original_chunk.max < other_chunk.max:
            # we advance only the original chunk
            original_chunk = get_next_chunk(original_chunks_enumerator)
            other_chunk = accumulated_union
            continue

        if other_chunk.max < original_chunk.max:
            original_chunk = accumulated_union
            other_chunk = get_next_chunk(other_chunks_enumerator)
            continue

        # Now for continuous dimensions we have one more complication to deal with: include_max
        if original_chunk.max == other_chunk.max \
                and isinstance(original_chunk, ContinuousDimension) \
                and original_chunk.include_max != other_chunk.include_max:

            if original_chunk.include_max and not other_chunk.include_max:
                # we only advance the other_chunk
                original_chunk = accumulated_union
                other_chunk = get_next_chunk(other_chunks_enumerator)
                continue
            if not original_chunk.include_max and other_chunk.include_max:
                original_chunk = get_next_chunk(original_chunks_enumerator)
                other_chunk = accumulated_union
                continue

        # Now if neither one of the above holds, means we have a union of two chunks that have the same max.
        # We can thus push that accumulated union into the result and advance both chunks.
        assert original_chunk.max == other_chunk.max
        if isinstance(original_chunk, ContinuousDimension):
            assert original_chunk.include_max == other_chunk.include_max

        result.push(accumulated_union)
        original_chunk = get_next_chunk(original_chunks_enumerator)
        other_chunk = get_next_chunk(other_chunks_enumerator)

    while other_chunk is not None:
        # We have exhausted all original chunks, but we still need to make sure that
        # all trailing other_chunks make it into the union.
        result.push(other_chunk)
        other_chunk = get_next_chunk(other_chunks_enumerator)

    num_chunks = sum(1 for chunk in result.enumerate_chunks())
    if num_chunks == 1:
        all_chunks = [chunk for chunk in result.enumerate_chunks()]
        only_chunk = all_chunks[0]
        return only_chunk
    return result


def empty_union_any(_, other):
    return other.copy()


union_implementations = {
    (ContinuousDimension, ContinuousDimension): continuous_union_continuous,
    (ContinuousDimension, CompositeDimension): continuous_union_composite,
    (ContinuousDimension, EmptyDimension): any_union_empty,
    (DiscreteDimension, DiscreteDimension): discrete_union_discrete,
    (DiscreteDimension, CompositeDimension): discrete_union_composite,
    (DiscreteDimension, EmptyDimension): any_union_empty,
    (OrdinalDimension, OrdinalDimension): ordinal_union_ordinal,
    (OrdinalDimension, EmptyDimension): any_union_empty,
    (CategoricalDimension, CategoricalDimension): categorical_union_categorical,
    (CategoricalDimension, EmptyDimension): any_union_empty,
    (CompositeDimension, ContinuousDimension): composite_union_continuous,
    (CompositeDimension, DiscreteDimension): composite_union_discrete,
    (CompositeDimension, CompositeDimension): composite_union_composite,
    (CompositeDimension, EmptyDimension): any_union_empty,
    (EmptyDimension, ContinuousDimension): empty_union_any,
    (EmptyDimension, DiscreteDimension): empty_union_any,
    (EmptyDimension, OrdinalDimension): empty_union_any,
    (EmptyDimension, CategoricalDimension): empty_union_any,
    (EmptyDimension, CompositeDimension): empty_union_any,
    (EmptyDimension, EmptyDimension): empty_union_any,
}


def universal_union_implementation(original, other):
    assert original.name == other.name
    assert_type_compatibility(original, other)

    specific_union_implementation = union_implementations.get((type(original), type(other)), None)
    if specific_union_implementation is None:
        raise TypeError(
            f"The difference operation is not supported for operands: "
            f"dimension {original.name} of type: {type(original)}, and "
            f"dimension {other.name} of type: {type(other)}."
        )
    return specific_union_implementation(original, other)

# CONTAINS IMPLEMENTATIONS
def continuous_contains_discrete(continuous, discrete):
    return discrete.min in continuous and discrete.max in continuous


def continuous_contains_continuous(original, other):
    return original.contains_continuous_dimension(other)


def continuous_contains_categorical(continuous, categorical):
    return categorical.is_numeric and all(element in continuous for element in categorical)


def continuous_contains_composite(original, other):
    return all(chunk in original for chunk in other.enumerate_chunks())


def any_contains_empty(_, __):
    return True


def discrete_contains_discrete(original, other):
    return other in original


def discrete_contains_composite(original, other):
    return all(chunk in original for chunk in other.enumerate_chunks())


def ordinal_contains_ordinal(original, other):
    return other in original


def categorical_contains_categorical(original, other):
    return other in original


def composite_contains_continuous(original, other):
    # We know that chunks within a composite dimension are discontinuous so 'other' being a
    # ContinuousDimension has to be fully contained within any single chunk.
    return any(other in chunk for chunk in original.enumerate_chunks())


def composite_contains_discrete(original, other):
    return any(other in chunk.payload for chunk in original.enumerate_chunks())


def composite_contains_composite(original, other):
    # TODO: this is quadratic. We can make it linear.
    return all(chunk in original for chunk in other.enumerate_chunks())


def empty_contains_any(_, other):
    # NOTA BENE: from the space/subspace standpoint it's useful to say that emptiness contains emptiness
    return isinstance(other, EmptyDimension)


contains_implementations = {
    (ContinuousDimension, DiscreteDimension): continuous_contains_discrete,
    (ContinuousDimension, ContinuousDimension): continuous_contains_continuous,
    (ContinuousDimension, OrdinalDimension): continuous_contains_categorical,
    (ContinuousDimension, CategoricalDimension): continuous_contains_categorical,
    (ContinuousDimension, CompositeDimension): continuous_contains_composite,
    (ContinuousDimension, EmptyDimension): any_contains_empty,
    (DiscreteDimension, DiscreteDimension): discrete_contains_discrete,
    (DiscreteDimension, CompositeDimension): discrete_contains_composite,
    (DiscreteDimension, EmptyDimension): any_contains_empty,
    (OrdinalDimension, OrdinalDimension): ordinal_contains_ordinal,
    (OrdinalDimension, EmptyDimension): any_contains_empty,
    (CategoricalDimension, CategoricalDimension): categorical_contains_categorical,
    (CategoricalDimension, EmptyDimension): any_contains_empty,
    (CompositeDimension, ContinuousDimension): composite_contains_continuous,
    (CompositeDimension, DiscreteDimension): composite_contains_discrete,
    (CompositeDimension, CompositeDimension): composite_contains_composite,
    (CompositeDimension, EmptyDimension): any_contains_empty,
    (EmptyDimension, ContinuousDimension): empty_contains_any,
    (EmptyDimension, DiscreteDimension): empty_contains_any,
    (EmptyDimension, OrdinalDimension): empty_contains_any,
    (EmptyDimension, CategoricalDimension): empty_contains_any,
    (EmptyDimension, CompositeDimension): empty_contains_any,
    (EmptyDimension, EmptyDimension): empty_contains_any,
}


def universal_contains_implementation(original, other):
    if original.name != other.name:
        return False

    assert_type_compatibility(original, other)

    specific_contains_implementation = contains_implementations.get((type(original), type(other)), None)
    if specific_contains_implementation is None:
        raise TypeError(
            f"The difference operation is not supported for operands: "
            f"dimension {original.name} of type: {type(original)}, and "
            f"dimension {other.name} of type: {type(other)}."
        )
    return specific_contains_implementation(original, other)


def universal_equals_implementation(original, other):
    return original in other and other in original


def universal_intersects_implementation(original, other):
    return not isinstance(original.intersection(other), EmptyDimension)


## Now that we have all the implementations, time to do some monkey patching.

all_dimension_types = [
    ContinuousDimension,
    DiscreteDimension,
    CategoricalDimension,
    OrdinalDimension,
    CompositeDimension,
    EmptyDimension
]

for dimension_type in all_dimension_types:
    dimension_type.intersection = universal_intersection_implementation
    dimension_type.difference = universal_difference_implementation
    dimension_type.union = universal_union_implementation
    dimension_type.contains_dimension = universal_contains_implementation
    dimension_type.equals = universal_equals_implementation
    dimension_type.intersects = universal_intersects_implementation
