//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfigMemoryRegion.cpp
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
// NAME: SharedMemoryRegionView<SharedConfigMemoryRegion>::InitializeMemoryRegion
//
// PURPOSE:
//  Initializes memory region responsible for shared configs.
//
// RETURNS:
//  SharedConfigMemoryRegion.
//
// NOTES:
//
template<>
Internal::SharedConfigMemoryRegion& SharedMemoryRegionView<Internal::SharedConfigMemoryRegion>::InitializeMemoryRegion()
{
    Internal::SharedConfigMemoryRegion& sharedConfigMemoryRegion = MemoryRegion();

    // Initialize the shared config dictionary.
    //
    HRESULT hr = InitializeSharedConfigDictionary(
        sharedConfigMemoryRegion.SharedConfigDictionary,
        sharedConfigMemoryRegion.MemoryHeader,
        sizeof(Internal::SharedConfigMemoryRegion));

    // Terminate if we are unable to allocate an array for the shared config dictionary.
    //
    MLOS_RETAIL_ASSERT(SUCCEEDED(hr));

    return sharedConfigMemoryRegion;
}
}
}
