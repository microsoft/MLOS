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

template<class K, class V>
class SmartCacheImpl
{
public:
    class CacheEntry
    {
    public:
        K Key;
        V* Value;
    };

private:
    int m_size = 16;
    std::unique_ptr<CacheEntry*[]> m_cacheBuffer;

    // Mlos Tunable Component Config.
    //
    Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig>& m_config;

public:
    SmartCacheImpl(Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig>& config);
    ~SmartCacheImpl();

    bool Contains(K key);
    V* Get(K key);
    void Push(K key, V* value);
    K FindLargestKeyUpTo(K upperBound, K defaultKey);
    void Reconfigure();
};

template<class K, class V>
SmartCacheImpl<K, V>::SmartCacheImpl(Mlos::Core::ComponentConfig<SmartCache::SmartCacheConfig>& config)
  : m_config(config)
{
    m_size = 0;
    m_cacheBuffer = nullptr;

    // Apply initial configuration.
    //
    Reconfigure();
}

template<class K, class V>
SmartCacheImpl<K, V>::~SmartCacheImpl()
{
    for (int i = 0; i < m_size; i++)
    {
        if (m_cacheBuffer[i] != nullptr)
        {
            delete m_cacheBuffer[i];
        }
    }

    m_cacheBuffer.reset();
}

template<class K, class V>
bool SmartCacheImpl<K, V>::Contains(K key)
{
    if (m_config.TelemetryBitMask & 1) // 1 is KeyAccessEvent flag
    {
        SmartCache::CacheRequestEventMessage message;
        message.CacheAddress = reinterpret_cast<uint64_t>(this);
        message.KeyValue = key;
        m_config.SendTelemetryMessage(message);
    }

    CacheEntry* temp = m_cacheBuffer[key % m_size];
    if (temp == nullptr || temp->Key != key)
    {
        return false;
    }

    return true;
}

template<class K, class V>
V* SmartCacheImpl<K, V>::Get(K key)
{
    if (!Contains(key))
    {
        return nullptr;
    }

    return m_cacheBuffer[key % m_size]->Value;
}

template<class K, class V>
void SmartCacheImpl<K, V>::Push(K key, V* value)
{
    if (m_config.TelemetryBitMask & 1) // 1 is KeyAccessEvent flag
    {
        SmartCache::CacheRequestEventMessage message;
        message.CacheAddress = reinterpret_cast<uint64_t>(this);
        message.KeyValue = key;
        m_config.SendTelemetryMessage(message);
    }

    CacheEntry* existingEntry = m_cacheBuffer[key % m_size];
    if (existingEntry == nullptr)
    {
        existingEntry = new CacheEntry();
        m_cacheBuffer[key % m_size] = existingEntry;
    }

    existingEntry->Key = key;
    delete existingEntry->Value;
    existingEntry->Value = value;

    return;
}

template<class K, class V>
K SmartCacheImpl<K, V>::FindLargestKeyUpTo(K upperBound, K defaultKey)
{
    K largestSoFar = defaultKey;

    for (int i = 0; i < m_size; i++)
    {
        if (m_cacheBuffer[i] == nullptr)
        {
            continue;
        }

        if (m_cacheBuffer[i]->Key > largestSoFar&& m_cacheBuffer[i]->Key <= upperBound)
        {
            largestSoFar = m_cacheBuffer[i]->Key;
        }
    }

    return largestSoFar;
}

template<class K, class V>
void SmartCacheImpl<K, V>::Reconfigure()
{
    for (int i = 0; i < m_size; i++)
    {
        if (m_cacheBuffer[i] != nullptr)
        {
            delete m_cacheBuffer[i];
        }
    }

    m_cacheBuffer.reset();

    // Copy configuration.
    //
    m_size = m_config.CacheSize;

    // Reconfigure cache with the new settings.
    //
    m_cacheBuffer = std::make_unique<CacheEntry*[]>(m_size);

    for (int i = 0; i < m_size; i++)
    {
        m_cacheBuffer[i] = nullptr;
    }
}

class FibonacciValue
{
public:
    uint64_t previous;
    uint64_t current;
};

uint64_t fibonacci(uint64_t sequenceNumber, SmartCacheImpl<uint64_t, FibonacciValue>& existingCache)
{
    uint64_t temp;
    uint64_t previous = 1;
    uint64_t current = 1;

    uint64_t maxCachedSequenceNumber = existingCache.FindLargestKeyUpTo(sequenceNumber, 2);
    FibonacciValue* newCacheEntry = nullptr;

    if (maxCachedSequenceNumber > 2)
    {
        // std::cout << "Cache hit at: " << maxCachedSequenceNumber << "for target: " << sequenceNumber << std::endl;
        FibonacciValue* existingEntry = existingCache.Get(maxCachedSequenceNumber);
        previous = existingEntry->previous;
        current = existingEntry->current;
    }

    for (uint64_t i = maxCachedSequenceNumber; i < sequenceNumber; i++)
    {
        temp = previous;
        previous = current;
        current = previous + temp;

        newCacheEntry = new FibonacciValue();
        newCacheEntry->previous = previous;
        newCacheEntry->current = current;

        existingCache.Push(i, newCacheEntry);
    }

    return current;
}
