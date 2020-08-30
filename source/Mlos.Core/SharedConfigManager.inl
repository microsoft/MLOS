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
template <typename T>
HRESULT SharedConfigManager::CreateOrUpdateFrom(ComponentConfig<T>& componentConfig)
{
    // Ensure there is allocated and registered shared config memory region.
    //
    if (!m_sharedConfigMemRegionView.Buffer.Pointer)
    {
        HRESULT hr = RegisterSharedConfigMemoryRegion();
        if (FAILED(hr))
        {
            return hr;
        }
    }

    Internal::SharedConfigMemoryRegion& memoryRegion = m_sharedConfigMemRegionView.MemoryRegion();

    uint32_t slotIndex;
    uint32_t probingCount = 0;

    Proxy::Mlos::Core::Internal::UIntArray configsArray(m_sharedConfigMemRegionView.Buffer, memoryRegion.ConfigsArrayOffset);

    uint32_t elementCount = configsArray.Count();

    while (true)
    {
        slotIndex = TProbingPolicy::CalculateIndex(static_cast<T>(componentConfig), probingCount, elementCount);

        uint32_t offset = configsArray.Elements()[slotIndex];
        if (offset == 0)
        {
            // We found empty slot.
            //
            break;
        }

        SharedConfigHeader* sharedConfigHeader = reinterpret_cast<SharedConfigHeader*>(reinterpret_cast<byte*>(&memoryRegion) + offset);
        if (sharedConfigHeader->CodegenTypeIndex == TypeMetadataInfo::CodegenTypeIndex<T>())
        {
            // The same type, now compare the config key.
            //
            if (componentConfig.CompareKey(sharedConfigHeader))
            {
                // We found the shared config, update local config instance.
                //
                componentConfig.Bind(reinterpret_cast<typename ComponentConfig<T>::SharedConfigType*>(sharedConfigHeader));
                componentConfig.Update();

                return S_OK;
            }
        }
    }

    // Shared config has not been found, create a new entry.
    //

    // Allocate memory for shared component config in the shared memory region.
    //
    const uint64_t sharedConfigSize = sizeof(typename ComponentConfig<T>::SharedConfigType) + ObjectSerialization::GetSerializedSize(static_cast<T>(componentConfig));

    uint32_t allocatedOffset;
    HRESULT hr = AllocateInSharedConfigMemoryRegion(
        memoryRegion,
        sharedConfigSize,
        allocatedOffset);
    if (FAILED(hr))
    {
        return hr;
    }

    // #TODO weird api, bind those together
    // Copy initial config values.
    //
    typename ComponentConfig<T>::SharedConfigType* sharedConfig = reinterpret_cast<typename ComponentConfig<T>::SharedConfigType*>(reinterpret_cast<byte*>(&memoryRegion) + allocatedOffset);
    sharedConfig->Initialize(static_cast<T>(componentConfig));

    // Update local config.
    //
    componentConfig.Bind(sharedConfig);

    // #TODO
    // Serialize
    //
    ObjectSerialization::Serialize(BytePtr(&componentConfig.m_sharedConfig->m_config), static_cast<T>(componentConfig));

    // Update hash_map
    //
    configsArray.Elements()[slotIndex] = allocatedOffset;

    // Update address #TODO revisit what is going on.
    //
    sharedConfig->m_header.Address.Offset = allocatedOffset;
    sharedConfig->m_header.Address.MemoryRegionId = memoryRegion.MemoryHeader.MemoryRegionId;

    return S_OK;
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
template <typename T>
HRESULT SharedConfigManager::Lookup(ComponentConfig<T>& componentConfig)
{
    if (!m_sharedConfigMemRegionView.Buffer.Pointer)
    {
        return E_NOT_SET;
    }

    Internal::SharedConfigMemoryRegion& memoryRegion = m_sharedConfigMemRegionView.MemoryRegion();

    uint32_t slotIndex;
    uint32_t probingCount = 0;

    Proxy::Mlos::Core::Internal::UIntArray configsArray(m_sharedConfigMemRegionView.Buffer, memoryRegion.ConfigsArrayOffset);

    uint32_t elementCount = configsArray.Count();

    while (true)
    {
        slotIndex = TProbingPolicy::CalculateIndex(static_cast<T>(componentConfig), probingCount, elementCount);

        uint32_t offset = configsArray.Elements()[slotIndex];
        if (offset == 0)
        {
            // We found empty slot.
            //
            break;
        }

        SharedConfigHeader* sharedConfigHeader = reinterpret_cast<SharedConfigHeader*>(reinterpret_cast<byte*>(&memoryRegion) + offset);
        if (sharedConfigHeader->CodegenTypeIndex == TypeMetadataInfo::CodegenTypeIndex<T>())
        {
            // The same type, now compare the config key.
            //
            if (componentConfig.CompareKey(sharedConfigHeader))
            {
                // We found the shared config, update local config instance.
                //
                componentConfig.Bind(reinterpret_cast<typename ComponentConfig<T>::SharedConfigType*>(sharedConfigHeader));
                componentConfig.Update();

                return S_OK;
            }
        }
    }

    return E_NOT_SET;
}

}
}
