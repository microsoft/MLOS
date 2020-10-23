//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ProbingPolicy.h
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
template<typename THash>
struct TLinearProbing
{
    template<typename TKey>
    static uint32_t CalculateIndex(
        _In_ TKey codegenKey,
        _Inout_ uint32_t& probingCount,
        _In_ uint32_t elementCount);
};
}
}
}
