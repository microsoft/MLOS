//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Hash.h
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
// Checks whether THashFunction is a hash function type.
//
template<typename THashFunction>
struct is_hash_function
{
    static constexpr bool value = false;
};

// Hash implementation.
//
template<typename THashValue, typename THashFunction>
struct Hash
{
public:
    template<typename T>
    inline static THashValue CombineHashValue(THashValue hashValue, const T& value)
    {
        return THashFunction::CombineHashValue(hashValue, reinterpret_cast<const byte*>(&value), sizeof(value));
    }

    template<typename T>
    inline static THashValue GetHashValue(const T& value)
    {
        static_assert(is_hash_function<THashFunction>::value, "THashFunction is not valid hash function.");
        static_assert(std::is_integral<THashValue>::value, "THashValue is not integral type.");
        static_assert(std::is_arithmetic<THashValue>::value, "THashValue is not arithmetic type.");

        return THashFunction::GetHashValue(reinterpret_cast<const byte*>(&value), sizeof(value));
    }
};
}
}
}
