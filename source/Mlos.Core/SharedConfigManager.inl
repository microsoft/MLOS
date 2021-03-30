//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfigManager.inl
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
using TProbingPolicy = Collections::TLinearProbing<Collections::FNVHash<uint32_t>>;

//----------------------------------------------------------------------------
// NAME: SharedConfigManager::CreateOrUpdateFrom
//
// PURPOSE:
//  If component config has been registered, function updates a local config and returns.
//  Otherwise, it creates a config in the shared memory.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
template<typename T>
HRESULT SharedConfigManager::CreateOrUpdateFrom(_Inout_ ComponentConfig<T>& componentConfig)
{
    // Ensure there is allocated and registered shared config memory region.
    //
    if (m_sharedConfigMemoryRegionView.IsInvalid())
    {
        return E_NOT_SET;
    }

    Internal::SharedConfigDictionary& sharedConfigDictionary = m_sharedConfigMemoryRegionView.MemoryRegion().SharedConfigDictionary;

    return CreateOrUpdateFrom(sharedConfigDictionary, componentConfig);
}

//----------------------------------------------------------------------------
// NAME: SharedConfigManager::CreateOrUpdateFrom
//
// PURPOSE:
//  If component config has been registered, function updates a local config and returns.
//  Otherwise, it creates a config in the shared config dictionary.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
template<typename T>
HRESULT SharedConfigManager::CreateOrUpdateFrom(
    _Inout_ Internal::SharedConfigDictionary& sharedConfigDictionary,
    _Inout_ ComponentConfig<T>& componentConfig)
{
    return Internal::SharedConfigDictionaryLookup<SharedConfigManager::TProbingPolicy>::CreateOrUpdateFromInSharedConfigDictionary(
        sharedConfigDictionary,
        componentConfig);
}

//----------------------------------------------------------------------------
// NAME: SharedConfigManager::LookupSharedConfig
//
// PURPOSE:
//  Locates the shared config.
//
// RETURNS:
//  HRESULT, E_NOT_SET if config is not found.
//
// NOTES:
//
template<typename T>
HRESULT SharedConfigManager::Lookup(_Inout_ ComponentConfig<T>& componentConfig)
{
    if (m_sharedConfigMemoryRegionView.IsInvalid())
    {
        return E_NOT_SET;
    }

    Internal::SharedConfigDictionary& sharedConfigDictionary = m_sharedConfigMemoryRegionView.MemoryRegion().SharedConfigDictionary;

    return Lookup(sharedConfigDictionary, componentConfig);
}

//----------------------------------------------------------------------------
// NAME: SharedConfigManager::LookupSharedConfig
//
// PURPOSE:
//  Locates the shared config.
//
// RETURNS:
//  HRESULT, E_NOT_SET if config is not found.
//
// NOTES:
//
template<typename T>
HRESULT SharedConfigManager::Lookup(
    _Inout_ Internal::SharedConfigDictionary& sharedConfigDictionary,
    _Inout_ ComponentConfig<T>& componentConfig)
{
    return Internal::SharedConfigDictionaryLookup<SharedConfigManager::TProbingPolicy>::LookupInSharedConfigDictionary(
        sharedConfigDictionary,
        componentConfig);
}
}
}
