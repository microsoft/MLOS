# Optimizer Monitoring

## Motivation
The goal of this document is to outline the process of monitoring the optimizers, enumerate the metrics we wish to collect and the tools required to do so. 


## What we wish to monitor
For each optimizer we should be able to:
1. View it's current configuration (done).
1. View all the data that it was trained on.
1. View the state of the surrogate models:
    1. Have they been fitted?
    1. How many times has it been refitted?
    1. In case of an ensemble: has each of the component models been fitted?
    1. What are the values of goodness of fit measures?
    1. How many samples did the model consume?
    1. What exact data was each model trained on?
    1. Which of the objectives is the model predicting?
    1. Data specific to each model class. For example for a Decision Tree:
        1. Number of leafs
        1. Leaf statistics (sample mean, sample var, count)
        1. Depth and shape
        1. Splits

It makes sense for all of that information (except for the exact data) to be maintained by the model, and presented upon request. Storing multiple copies of data seems to be heavy overhead, so we should avoid it if at all possible. This problem will be solved by the introduction of DataSets and DataSetViews.

## Representing the state
It might be tempting to create a dictionary to store all of this data. I think such hash-map-oriented programming paradigm will quickly deteriorate, especially as more and more people begin contributing.

So a better approach would be to have a base class that stores (in common format) information common to all model classes. For each model we could derive a specialized class, that stores the more specific information.


### Serializing the state
We will have to be able to send this data over gRPC, so we must be mindful of how to serialize/deserialize it. Options include:
* Defining this struct in a .proto file and populating it directly.
* Serializing the struct to json.
* Serializing the struct using pickle.

The problem with .proto approach is that this becomes part of the API and will make changing anything unnecessarily hard.

The problem with json is that writing json serializer is extra work.

The problem with pickle is that only Python can deserialize it. But since we only need to deserialize in Python for the foreseeable future, we will go with this option. However, to hedge our bets, I'll wrap the calls to pickle.dumps and pickle.loads inside a .serialize(), .deserialize() functions to allow for an implementation change down the road (e.g. if we want to monitor the optimizer from C# or Julia).



