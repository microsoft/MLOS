//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfigManager.h
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
class MlosContext;

//----------------------------------------------------------------------------
// NAME: SharedConfigManager
//
// PURPOSE:
//  Class provies methods to manage shared configurations.
//  It is also resposible for managing the shared config memory region.
//
// NOTES:
//
class SharedConfigManager
{
public:
    // Open hash table probing policy.
    //
    using TProbingPolicy = Collections::TLinearProbing<Collections::FNVHash<uint32_t>>;

public:
    SharedConfigManager(MlosContext& mlosContext) noexcept;

    ~SharedConfigManager();

    // Creates a new shared config or updates from the shared config in the shared memory.
    //
    template<typename T>
    HRESULT CreateOrUpdateFrom(ComponentConfig<T>& componentConfig);

    // Creates a new shared config or updates from the shared config in the shared memory.
    //
    template<typename T>
    static HRESULT CreateOrUpdateFrom(
        Internal::SharedConfigDictionary& sharedConfigDictionary,
        ComponentConfig<T>& componentConfig);

    // Locates the component config.
    //
    template<typename T>
    HRESULT Lookup(ComponentConfig<T>& componentConfig);

    // Locates the component config.
    //
    template<typename T>
    static HRESULT Lookup(Internal::SharedConfigDictionary& sharedConfigDictionary, ComponentConfig<T>& componentConfig);

private:
    MlosContext& m_mlosContext;

    HRESULT RegisterSharedConfigMemoryRegion();

    // Shared memory region used to keep all the shared component configurations.
    // #TODO we might need more than one memory region for the configuration objects.
    //
    SharedMemoryRegionView<Internal::SharedConfigMemoryRegion> m_sharedConfigMemRegionView;

public:
    // Indicates if we should cleanup OS resources when closing the shared memory map view.
    // No-op on Windows.
    //
    bool CleanupOnClose;
};
}
}
