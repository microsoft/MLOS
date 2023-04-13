# Space Adapters

It is often the case in black-box optimization that we need to perform some kind of *transformation* between the original parameter space (i.e., input space), and the space considered by the underlying optimizer (i.e., target parameters space).
Two examples of such transformations include (1) applying log space on the values of one (or more) parameters, or (2) employing parameter value discretization to reduce the number of unique considered values.
While trivial transformations, like the two above, might be provided by `ConfigSpace`, more complicated ones are not.

A *space adapter* provides the user the ability to define such an arbitrary transformation.
This is achieved using an implementation of the abstract `BaseSpaceAdapter` class.
To facilitate the custom transformation functionality, the user should provide implementation for the following three methods:

- `transform`, which provides the logic for translating a given configuration *from* the target parameter space to the original one.
- `inverse_transform`, which translates a configuration *from* the original parameter space to the target one.
- `target_parameter_space`, which returns the `ConfigSpace` definition of the target parameter space, which is typically based upon the input original space.

More technical details can be found in `adapter.py`.

Please note that currently space adapters cannot be used in conjunction with user-provided context. We plan to investigate whether it is possible to support such a functionality in the future.

## LlamaTune Space Adapter

Currently, `mlos_core` supports a single space adapter, `LlamaTuneSpaceAdapter`, which implements the LlamaTune methodology described in this [VLDB'22 research paper](https://www.vldb.org/pvldb/vol15/p2953-kanellis.pdf).
It has been shown experimentally that optimizers (like SMAC) that leverage LlamaTune can identify good-performing parameter configurations in a more *sample-efficient* manner, using on average 5.6x fewer samples.

In summary, LlamaTune leverages expert domain knowledge for DBMSs to construct an *artificial low-dimensional* search space that is more effectively explored by the optimizer.
This low-dimensional space is constructed using a random linear projection of the original parameter space, i.e., the parameters of the target parameter space are *linear combinations* of the parameters of the original one.
Further, LlamaTune allows the user to provide a list of *special values* for a subset of the original parameters; these special values will then be prioritized during the optimization process.
Finally, the user can optionally specify the maximum number of unique values for each parameter.

### Usage Example

`LlamaTuneSpaceAdapter` receives up to three hyperparameters:

- `num_low_dims`, the dimensionality of the target parameter space (defaults to 16). Needs to be smaller than the original space.
- `special_param_values`, one (or more) special values for each parameter. The user can also define the degree of prioritization (defaults to 20%).
- `max_unique_values`, the maximum number of unique values per parameter (defaults to 10,000).

The user can employ `LlamaTuneSpaceAdapter` when initializing the `mlos_core` optimizer, using `OptimizerFactory`, as follows:

```python
llamatune_optimizer = OptimizerFactory.create(
    ...
    space_adapter_type=SpaceAdapterType.LLAMATUNE,
    space_adapter_kwargs=<llamatune_kwargs>,
)
```

### Known Limitations

The random projection method employed by LlamaTune is inherently one-directional, i.e., from the target parameter space to the original one. This poses no issues in the typical use case, where each `.suggest()` call to the `mlos_core` optimizer is strictly followed by the corresponding `.register()` call. Yet, if the user wishes to register points (i.e., configurations) that were **not** previously suggested by the optimizer (e.g., bootstraping the optimizer using samples from some other run), it would normally be impossible.

In an effort to accommodate this use-case, we have devise a method, which tries to approximate the reverse projection of those user-provided points. Given that the original random projection utilizes a projection matrix *P*, our method computes its [Moore–Penrose pseudo-inverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse) matrix *P'*. Then, using *P'* we (approximately) project the points from the original parameter space to the target one. Please note that this method is *highly experimental*, and thus we provide no guarantees on how well (or not) it performs. More technical information can be found in the `_try_generate_approx_inverse_mapping` method inside `llamatune.py`.
