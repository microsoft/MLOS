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

    globalMemoryRegion.RegisteredSettingsAssemblyCount.store(1);

    return globalMemoryRegion;
}
}
}
