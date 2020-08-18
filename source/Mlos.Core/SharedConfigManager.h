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

class SharedConfigManager
{
public:
    SharedConfigManager(MlosContext& mlosContext) noexcept;

    // Creates a new shared config or updates from the shared config in the shared memory.
    //
    template<typename T>
    HRESULT CreateOrUpdateFrom(ComponentConfig<T>& componentConfig);

    // Locates the component config.
    //
    template<typename T>
    HRESULT Lookup(ComponentConfig<T>& componentConfig);

private:
    MlosContext& m_mlosContext;

    HRESULT RegisterSharedConfigMemoryRegion();

    // Shared memory region used to keep all the shared component configurations.
    // #TODO we might need more than one memory region for the configuration objects.
    //
    SharedMemoryRegionView<Internal::SharedConfigMemoryRegion> m_sharedConfigMemRegionView;
};
}
}
