# Hypergrid Adapters

## Motivation

### Categorical to numeric projections
The goal of adapters is to make a broader class of hypergrids compatible with any surrogate model. The chief problem in absence of adapters is that some models (RERF, DecisionTreeRegressionModel)
can only operate on numeric datatypes, but the configuration for many components includes strings, and booleans as well. A suitable adapter will map such categorical dimensions into numeric ones 
and allow transparent projection of observations and suggestions between the components and the regression models.

### Renames and hierarchy flattening
Another use case is that from the smart components perspective hypergrids can be hierarchical, but some models can only work with flat data. A suitable adapter will flatten the hierarchy when 
feeding data to the model, and rebuild the hierarchy when emitting suggestions/predictions from the model.

### Imputing values
Some models work well with missing values, but some models cannot handle them. An imputing adapter could be used to impute values according to a specified rule. We will start with a constant, 
but more sophisticated imputing strategies will be enabled.

### Skipping dimensions
Sometimes we would like to filter out dimensions. One way to do it is to use an adapter.

### Transformations on input space
PCA etc. standardizing/normalizing the input space.


## Requirements
1. An adapter has to derive from the Hypergrid base class (and thus implement its interface). They expose the interface of the target.
1. Adapters must be stackable - we should be able to apply a renaming adapter on top of an imputing adapter.
1. Adapters must maintain all mappings they create and we must be able to serialize/deserialize adapters objects.
1. Adapters must be able to project Point and pandas.DataFrame objects.
1. We need json encoders/decoders for each or maybe pickle is enough...
