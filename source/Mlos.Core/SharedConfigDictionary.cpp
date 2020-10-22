//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfigDictionary.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

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
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Check_return_
HRESULT InitializeSharedConfigDictionary(
    SharedConfigDictionary& sharedConfigDictionary,
    MemoryRegion& memoryRegion,
    int32_t allocationBlockOffset)
{
    // Initialize allocator.
    //
    HRESULT hr = InitializeArenaAllocator(sharedConfigDictionary.Allocator, memoryRegion, allocationBlockOffset);
    if (FAILED(hr))
    {
        return hr;
    }

    uint32_t allocatedElementOffset;

    // Allocate array for shared config offsets.
    //
    uint32_t elementCount = 2048;
    hr = AllocateInMemoryRegion(
        sharedConfigDictionary.Allocator,
        sizeof(UIntArray) + (sizeof(uint32_t) * elementCount),
        allocatedElementOffset);
    if (FAILED(hr))
    {
        return hr;
    }

    // Update configsArrayOffset to use sharedConfigDictionary pointer.
    //
    sharedConfigDictionary.OffsetToConfigsArray =
        allocatedElementOffset - static_cast<int32_t>(BytePtr(&sharedConfigDictionary).Pointer - BytePtr(&memoryRegion).Pointer);

    // Initialize the allocated array.
    //
    UIntArray& configsOffsetArray =
        *reinterpret_cast<UIntArray*>(BytePtr(&sharedConfigDictionary).Pointer +  sharedConfigDictionary.OffsetToConfigsArray);
    configsOffsetArray.Count = elementCount;

    return hr;
}
}
}
}
