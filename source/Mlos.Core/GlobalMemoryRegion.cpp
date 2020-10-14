//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: GlobalMemoryRegion.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

using namespace Mlos::Core;

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: SharedMemoryRegionView<GlobalMemoryRegion>::InitializeMemoryRegion
//
// PURPOSE:
//  Initializes global memory region.
//
// RETURNS:
//  GlobalMemoryRegion.
//
// NOTES:
//
template<>
Internal::GlobalMemoryRegion& SharedMemoryRegionView<Internal::GlobalMemoryRegion>::InitializeMemoryRegion()
{
    Internal::GlobalMemoryRegion& globalMemoryRegion = MemoryRegion();

    // Initialize properties.
    //
    globalMemoryRegion.TotalMemoryRegionCount = 1;

    // Mlos.NetCore is always registered first.
    //
    globalMemoryRegion.RegisteredSettingsAssemblyCount.store(1);

    // Initialize the shared config dictionary.
    //
    HRESULT hr = InitializeSharedConfigDictionary(
        globalMemoryRegion.SharedConfigDictionary,
        globalMemoryRegion.MemoryHeader,
        sizeof(Internal::GlobalMemoryRegion));

    // Terminate if we are unable to allocate an array for the shared config dictionary.
    //
    MLOS_RETAIL_ASSERT(SUCCEEDED(hr));

    return globalMemoryRegion;
}
}
}
