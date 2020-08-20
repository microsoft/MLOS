//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: Utils.h
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
//----------------------------------------------------------------------------
// NAME: lower_uint32
//
// PURPOSE:
//
// NOTES:
//
inline constexpr uint32_t lower_uint32(const uint64_t value)
{
    return static_cast<uint32_t>(value);
}

//----------------------------------------------------------------------------
// NAME: higher_uint32
//
// PURPOSE:
//
// NOTES:
//
inline constexpr uint32_t higher_uint32(const uint64_t value)
{
    return static_cast<uint32_t>((value >> 32) & std::numeric_limits<uint32_t>::max());
}

//----------------------------------------------------------------------------
// NAME: align
//
// PURPOSE:
//
// NOTES:
//
template<int N>
inline constexpr int32_t align(const int32_t size)
{
    return ((size + N - 1) / N) * N;
}

//----------------------------------------------------------------------------
// NAME: align
//
// PURPOSE:
//
// NOTES:
//
template<int N>
inline constexpr size_t align(const size_t size)
{
    return ((size + N - 1) / N) * N;
}

//----------------------------------------------------------------------------
// NAME: most_significant_bit
//
// PURPOSE:
//
// NOTES:
//
template<typename T>
inline constexpr uint8_t most_significant_bit(T value)
{
    uint8_t result = 0;
    while (value >>= 1)
    {
        result++;
    }

    return result;
}
}
}
