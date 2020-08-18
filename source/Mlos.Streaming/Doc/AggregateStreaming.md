# Aggregates on the telemetry streams

## Intro


## Processing models

|                              | Single return value | Multiple return values |
|------------------------------|---------------------|------------------------|
| Pull/Synchronous/Interactive | T                   | IEnumerable\<T>        |
| Push/Asynchronous/Reactive   | Task\<T>            | IObservable\<T>        |


## MLOS Telemetry channel

### Processing events

- why not async:
  - introduces dedicated processing tasks
  - additional latency introduced by AsyncQueue

- why we need a push model

### Linq operators on observable streams


### Merging streams operator

### Collecting the results
- *in progress*

### Performance improvements
- *in progress*
