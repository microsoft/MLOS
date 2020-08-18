//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: FNVHashFunction.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

namespace Mlos
{
namespace Core
{
namespace Collections
{
// #TODO change interace
// add final mix
//

template<typename THashValue>
struct FNVHashFunction
{
private:
    constexpr static THashValue Prime();
    constexpr static THashValue OffsetBasis();

public:
    static inline THashValue CombineHashValue(THashValue hashValue, const byte* buffer, uint32_t length)
    {
        for (uint32_t i = 0; i < length; i++)
        {
            hashValue = buffer[i] ^ hashValue;
            hashValue *= Prime();
        }

        return hashValue;
    }

    static inline THashValue GetHashValue(const byte* buffer, uint32_t length)
    {
        THashValue hashValue = OffsetBasis();

        return CombineHashValue(hashValue, buffer, length);
    }
};

template<>
constexpr uint32_t FNVHashFunction<uint32_t>::OffsetBasis()
{
    return 0x811c9dc5;
}

template<>
constexpr uint64_t FNVHashFunction<uint64_t>::Prime()
{
    return 0x00000100000001B3ul;
}

template<>
constexpr uint64_t FNVHashFunction<uint64_t>::OffsetBasis()
{
    return 0xcbf29ce484222325;
}

template<>
constexpr uint32_t FNVHashFunction<uint32_t>::Prime()
{
    return 0x01000193;
}

// Public hash.
//
template<typename THashValue>
using FNVHash = Hash<THashValue, FNVHashFunction<THashValue>>;

// FNVHash hash_function trait.
//
template<typename THashValue>
struct is_hash_function<FNVHashFunction<THashValue>>
{
    static constexpr bool value = true;
};
}
}
}
