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

    // Initialize memory allocator.
    //
    Internal::ArenaAllocator& allocator = sharedConfigMemoryRegion.Allocator;

    allocator.AllocationBlockOffset = static_cast<uint32_t>(align<256>(sizeof(Internal::SharedConfigMemoryRegion)));;
    allocator.AllocationBlockSize = static_cast<uint32_t>(
        sharedConfigMemoryRegion.MemoryHeader.MemoryRegionSize -
        sharedConfigMemoryRegion.Allocator.FreeOffset);

    allocator.FreeOffset = allocator.AllocationBlockOffset;
    allocator.AllocationCount = 0;
    allocator.LastAllocatedOffset = 0;

    // Allocate array for shared config offsets.
    //
    uint32_t elementCount = 2048;
    HRESULT hr = AllocateInSharedConfigMemoryRegion(
        sharedConfigMemoryRegion,
        sizeof(Internal::UIntArray) + (sizeof(uint32_t) * elementCount),
        sharedConfigMemoryRegion.ConfigsArrayOffset);

    // Terminate if we are unable to allocate a shared config hashmap.
    //
    RETAIL_ASSERT(SUCCEEDED(hr));

    // Initialize the allocated array.
    //
    Internal::UIntArray& configsOffsetArray = GetCodegenObject<Internal::UIntArray>(sharedConfigMemoryRegion.ConfigsArrayOffset);
    configsOffsetArray.Count = elementCount;

    return sharedConfigMemoryRegion;
}

namespace Internal
{
//----------------------------------------------------------------------------
// NAME: AllocateMemoryInSharedMemoryRegion
//
// PURPOSE:
//  Allocates the memory in the shared memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//  Dummy allocator. Not thread safe.
//
//  #TODO revisit thread safety
//
HRESULT AllocateInSharedConfigMemoryRegion(
    Internal::SharedConfigMemoryRegion& sharedConfigMemoryRegion,
    uint64_t size,
    _Out_ uint32_t& offset)
{
    size += sizeof(Internal::AllocationEntry);

    Internal::ArenaAllocator& allocator = sharedConfigMemoryRegion.Allocator;

    if (allocator.FreeOffset + size >= sharedConfigMemoryRegion.MemoryHeader.MemoryRegionSize)
    {
        return E_OUTOFMEMORY;
    }

    // Update the address.
    //
    offset = allocator.FreeOffset;

    // Update memory region properties.
    //
    allocator.FreeOffset += static_cast<uint32_t>(align<64>(size));
    allocator.AllocationCount++;

    // Update last allocated entry.
    //
    if (allocator.LastAllocatedOffset != 0)
    {
        AllocationEntry* lastAllocationEntry = reinterpret_cast<AllocationEntry*>(
            reinterpret_cast<byte*>(&sharedConfigMemoryRegion) + allocator.LastAllocatedOffset);

        lastAllocationEntry->NextEntryOffset = offset;
    }

    // Update current allocated entry.
    //
    AllocationEntry* allocationEntry = reinterpret_cast<AllocationEntry*>(
        reinterpret_cast<byte*>(&sharedConfigMemoryRegion) + offset);
    allocationEntry->PrevEntryoffset = allocator.LastAllocatedOffset;

    allocator.LastAllocatedOffset = offset;

    // Skip the allocation entry.
    //
    offset += sizeof(Internal::AllocationEntry);

    return S_OK;
}
}
}
}
