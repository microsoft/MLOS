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
//  Class provides methods to manage shared configurations.
//  It is also responsible for managing the shared config memory region.
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
    SharedConfigManager() noexcept;

    ~SharedConfigManager();

    void AssignSharedConfigMemoryRegion(
        _In_ SharedMemoryRegionView<Internal::SharedConfigMemoryRegion>&& sharedConfigMemoryRegionView);

    // Creates a new shared config or updates from the shared config in the shared memory.
    //
    template<typename T>
    _Must_inspect_result_
    HRESULT CreateOrUpdateFrom(_Inout_ ComponentConfig<T>& componentConfig);

    // Creates a new shared config or updates from the shared config in the shared memory.
    //
    template<typename T>
    _Must_inspect_result_
    static HRESULT CreateOrUpdateFrom(
        _Inout_ Internal::SharedConfigDictionary& sharedConfigDictionary,
        _Inout_ ComponentConfig<T>& componentConfig);

    // Locates the component config.
    //
    template<typename T>
    _Must_inspect_result_
    HRESULT Lookup(ComponentConfig<T>& componentConfig);

    // Locates the component config.
    //
    template<typename T>
    _Must_inspect_result_
    static HRESULT Lookup(
        _Inout_ Internal::SharedConfigDictionary& sharedConfigDictionary,
        _Inout_ ComponentConfig<T>& componentConfig);

private:
    // Shared memory region used to keep all the shared component configurations.
    //
    SharedMemoryRegionView<Internal::SharedConfigMemoryRegion> m_sharedConfigMemoryRegionView;

public:
    // Indicates if we should cleanup OS resources when closing the shared memory map view.
    // No-op on Windows.
    //
    bool CleanupOnClose;

    friend class MlosContext;
};
}
}
