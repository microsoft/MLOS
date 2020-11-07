//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SmartCacheImpl.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

template<typename TKey, typename TValue>
class SmartCacheImpl
{
private:
    size_t m_cacheSize;

    std::list<TValue> m_elementSequence;

    std::unordered_map<TKey, typename std::list<TValue>::iterator> m_lookupTable;

    // Mlos Tunable Component Config.
    //
    Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig>& m_config;

public:
    SmartCacheImpl(Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig>& config);
    ~SmartCacheImpl();

    bool Contains(TKey key);
    TValue* Get(TKey key);
    void Push(TKey key, const TValue value);

    void Reconfigure();
};

template<typename TKey, typename TValue>
inline SmartCacheImpl<TKey, TValue>::SmartCacheImpl(Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig>& config)
  : m_config(config)
{
    m_cacheSize = 0;

    // Apply initial configuration.
    //
    Reconfigure();
}

template<class K, class V>
SmartCacheImpl<K, V>::~SmartCacheImpl()
{
}

template<typename TKey, typename TValue>
inline bool SmartCacheImpl<TKey, TValue>::Contains(TKey key)
{
    bool isInCache = m_lookupTable.find(key) != m_lookupTable.end();

    SmartCache::CacheRequestEventMessage msg;
    msg.ConfigId = m_config.ConfigId;
    msg.Key = key;
    msg.IsInCache = isInCache;

    m_config.SendTelemetryMessage(msg);

    return isInCache;
}

template<typename TKey, typename TValue>
inline TValue* SmartCacheImpl<TKey, TValue>::Get(TKey key)
{
    if (!Contains(key))
    {
        return nullptr;
    }

    // Find the element ref in the lookup table.
    //
    auto lookupItr = m_lookupTable.find(key);

    // Move the element to the beginning of the queue.
    //
    m_elementSequence.emplace_front(*lookupItr->second);
    m_elementSequence.erase(lookupItr->second);

    // As we moved the element, we need to update the element ref.
    //
    lookupItr->second = m_elementSequence.begin();

    return &m_elementSequence.front();
}

template<typename TKey, typename TValue>
inline void SmartCacheImpl<TKey, TValue>::Push(TKey key, const TValue value)
{
    // Find the element ref in the lookup table.
    //
    auto lookupItr = m_lookupTable.find(key);

    if (lookupItr == m_lookupTable.end())
    {
        if (m_elementSequence.size() == m_cacheSize)
        {
            // We reached the maximum cache size, evict the element based on the current policy.
            //
            if (m_config.EvictionPolicy == SmartCache::CacheEvictionPolicy::LeastRecentlyUsed)
            {
                auto evictedLookupItr = m_elementSequence.back();
                m_elementSequence.pop_back();
                m_lookupTable.erase(evictedLookupItr);
            }
            else if (m_config.EvictionPolicy == SmartCache::CacheEvictionPolicy::MostRecentlyUsed)
            {
                auto evictedLookupItr = m_elementSequence.front();
                m_elementSequence.pop_front();
                m_lookupTable.erase(evictedLookupItr);
            }
            else
            {
                // Unknown policy.
                //
                throw std::exception();
            }
        }

        m_elementSequence.emplace_front(value);
        auto elementItr = m_elementSequence.begin();

        m_lookupTable.emplace(key, elementItr);
    }
    else
    {
        // Enqueue new element to the beginning of the queue.
        //
        m_elementSequence.emplace_front(value);
        m_elementSequence.erase(lookupItr->second);

        // Update existing lookup.
        //
        lookupItr->second = m_elementSequence.begin();
    }

    return;
}

template<typename TKey, typename TValue>
inline void SmartCacheImpl<TKey, TValue>::Reconfigure()
{
    // Update the cache size from the latest configuration available in shared memory.
    //
    m_cacheSize = m_config.CacheSize;

    // Clear the cache.
    //
    m_elementSequence.clear();
    m_lookupTable.clear();

    // Adjust the number of buckets reserved for the cache (relative to the
    // max_load_factor) to match the new size.
    //
    m_lookupTable.reserve(m_cacheSize);
}
