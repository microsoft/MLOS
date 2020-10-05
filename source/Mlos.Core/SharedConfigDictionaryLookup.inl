//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfigDictionaryLookup.inl
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
// NAME: CreateOrUpdateFromInSharedConfigDictionary
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
template<typename TProbingPolicy>
template<typename T>
_Check_return_
HRESULT SharedConfigDictionaryLookup<TProbingPolicy>::CreateOrUpdateFromInSharedConfigDictionary(
    SharedConfigDictionary& sharedConfigDictionary,
    ComponentConfig<T>& componentConfig)
{
    uint32_t slotIndex;
    uint32_t probingCount = 0;

    BytePtr memoryRegionPtr(reinterpret_cast<byte*>(&sharedConfigDictionary) - sharedConfigDictionary.Allocator.OffsetToAllocator);

    Proxy::Mlos::Core::Internal::UIntArray configsArray(
        BytePtr(&sharedConfigDictionary),
        sharedConfigDictionary.OffsetToConfigsArray);

    uint32_t elementCount = configsArray.Count();

    while (true)
    {
        slotIndex = TProbingPolicy::CalculateIndex(static_cast<T>(componentConfig), probingCount, elementCount);

        uint32_t offsetToSharedConfig = configsArray.Elements()[slotIndex];
        if (offsetToSharedConfig == 0)
        {
            // We found empty slot.
            //
            break;
        }

        SharedConfigHeader* sharedConfigHeader =
            reinterpret_cast<SharedConfigHeader*>(memoryRegionPtr.Pointer + offsetToSharedConfig);
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

    // First, allocate memory for the shared component config in the shared memory region.
    //
    const uint64_t sharedConfigSize = sizeof(typename ComponentConfig<T>::SharedConfigType) +
        ObjectSerialization::GetSerializedSize(static_cast<T>(componentConfig));

    uint32_t allocatedOffset = 0;
    HRESULT hr = AllocateInMemoryRegion(
        sharedConfigDictionary.Allocator,
        sharedConfigSize,
        allocatedOffset);
    if (FAILED(hr))
    {
        return hr;
    }

    // Copy initial config values.
    //
    typename ComponentConfig<T>::SharedConfigType* sharedConfig =
        reinterpret_cast<typename ComponentConfig<T>::SharedConfigType*>(memoryRegionPtr.Pointer + allocatedOffset);
    sharedConfig->InitializeFromDefaultConfig(static_cast<T>(componentConfig));

    // Bind the local component config with the config in the shared memory.
    //
    componentConfig.Bind(sharedConfig);

    // Once the component is fully created, update the dictionary entry.
    //
    configsArray.Elements()[slotIndex] = allocatedOffset;

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: SharedConfigDictionaryLookup<TProbingPolicy>::LookupInSharedConfigDictionary
//
// PURPOSE:
//  Locates the shared config.
//
// RETURNS:
//  HRESULT, E_NOT_SET if config is not found.
//
// NOTES:
//
template<typename TProbingPolicy>
template<typename T>
_Check_return_
HRESULT SharedConfigDictionaryLookup<TProbingPolicy>::LookupInSharedConfigDictionary(
    SharedConfigDictionary& sharedConfigDictionary,
    ComponentConfig<T>& componentConfig)
{
    uint32_t slotIndex;
    uint32_t probingCount = 0;

    BytePtr memoryRegionPtr(reinterpret_cast<byte*>(&sharedConfigDictionary) - sharedConfigDictionary.Allocator.OffsetToAllocator);

    Proxy::Mlos::Core::Internal::UIntArray configsArray(
        BytePtr(&sharedConfigDictionary),
        sharedConfigDictionary.OffsetToConfigsArray);

    uint32_t elementCount = configsArray.Count();

    while (true)
    {
        slotIndex = TProbingPolicy::CalculateIndex(static_cast<T>(componentConfig), probingCount, elementCount);

        uint32_t offsetToSharedConfig = configsArray.Elements()[slotIndex];
        if (offsetToSharedConfig == 0)
        {
            // We found empty slot.
            //
            break;
        }

        SharedConfigHeader* sharedConfigHeader =
            reinterpret_cast<SharedConfigHeader*>(memoryRegionPtr.Pointer + offsetToSharedConfig);
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
}
