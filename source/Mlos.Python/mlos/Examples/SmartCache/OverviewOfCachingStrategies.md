# Overview of Caching Strategies and Algorithms

## Goal
The objective of this document is to describe various approaches to caching. The intent is to then implement a number of paramiterized caching algorithms and allow MLOS to select between them on a per-workload basis.

## Links
A loose list of sources consulted in this survey:
* https://medium.com/datadriveninvestor/all-things-caching-use-cases-benefits-strategies-choosing-a-caching-technology-exploring-fa6c1f2e93aa
* https://en.wikipedia.org/wiki/Cache_replacement_policies

## Potential Objectives
* average retrieval time/cost/latency (or other statistics: percentiles, CI's etc)
* hit ratio and miss ratio
* cache hit latency metrics (in case of a hit)
* data staleness metrics (distribution of time since last usage among all cache entries)

## Plausible Implementations/Approaches
* FIFO - a queue and a hash-map would work. Parameters: max_num_entries, max_size
* LIFO - a stack and a hash-map would work. Parameters: max_num_entries, max_size
* LRU - a linked list and a hash-map. Parameters: max_num_entries, max_size. There are variants descirbed here: https://en.wikipedia.org/wiki/Page_replacement_algorithm#Variants_on_LRU
* TLRU - time aware LRU or LRU with TTL
* MRU - most recently used. Apparently useful for random access patterns and cyclical access patterns 
* PLRU - pseudo-LRU. A set of heuristic and probability based approaches approximating LRU
* Random Replacement - we'd better be able to beat that
* Segmented LRU (SLRU) - a more complex strategy described in detail here: https://en.wikipedia.org/wiki/Cache_replacement_policies
