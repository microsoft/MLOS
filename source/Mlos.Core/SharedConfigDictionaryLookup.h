//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfigDictionaryLookup.h
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
namespace Internal
{
//----------------------------------------------------------------------------
// NAME: InitializeSharedConfigDictionary
//
// PURPOSE:
//  Initializes the shared config dictionary stored in the memory region.
//
// NOTES:
//  Lookup functions are implemented in SharedConfigDictionaryLookup<TProbingPolicy>.
//
_Check_return_
HRESULT InitializeSharedConfigDictionary(
    SharedConfigDictionary& sharedConfigDictionary,
    MemoryRegion& memoryRegion,
    int32_t allocationBlockOffset);

//----------------------------------------------------------------------------
// NAME: SharedConfigDictionaryLookup
//
// PURPOSE:
//  SharedConfigDictionary lookup implementation based on the given hash table probing policy.
//
// NOTES:
//
template<typename TProbingPolicy>
struct SharedConfigDictionaryLookup
{
private:
    // Creates a new shared config or updates from the shared config in the shared memory.
    //
    template<typename T>
    _Check_return_
    static HRESULT CreateOrUpdateFromInSharedConfigDictionary(
        SharedConfigDictionary& sharedConfigDictionary,
        ComponentConfig<T>& componentConfig);

    // Locates the component config.
    //
    template<typename T>
    _Check_return_
    static HRESULT LookupInSharedConfigDictionary(
        SharedConfigDictionary& sharedConfigDictionary,
        ComponentConfig<T>& componentConfig);

    friend class ::Mlos::Core::SharedConfigManager;
};
}
}
}
