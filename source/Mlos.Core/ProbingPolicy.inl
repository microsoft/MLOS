//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ProbingPolicy.inl
//
// Purpose:
//  Probing policy implementation.
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
template<typename TKey>
uint32_t TLinearProbing<THash>::CalculateIndex(
    _In_ TKey codegenKey,
    _Inout_ uint32_t& probingCount,
    _In_ const uint32_t elementCount)
{
    const uint32_t hashValue = TypeMetadataInfo::GetKeyHashValue<THash>(codegenKey);
    return (hashValue + probingCount++) % elementCount;
}
}
}
}
