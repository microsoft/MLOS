//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ArenaAllocator.cpp
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
// NAME: InitializeArenaAllocator
//
// PURPOSE:
//  Initializes the area allocator stored in the memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Check_return_
HRESULT InitializeArenaAllocator(
    ArenaAllocator& allocator,
    MemoryRegion& memoryRegion,
    int32_t firstAllocationOffset)
{
    allocator.OffsetToAllocator = static_cast<int32_t>(BytePtr(&allocator).Pointer - BytePtr(&memoryRegion).Pointer);

    allocator.FirstAllocationOffset = static_cast<uint32_t>(align<256>(firstAllocationOffset));
    allocator.AllocationBlockSize = static_cast<uint32_t>(memoryRegion.MemoryRegionSize - allocator.FirstAllocationOffset);

    allocator.FreeOffset = allocator.FirstAllocationOffset;
    allocator.AllocationCount = 0;
    allocator.LastAllocatedOffset = 0;

    return S_OK;
}

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
_Check_return_
HRESULT AllocateInMemoryRegion(
    ArenaAllocator& allocator,
    uint64_t size,
    _Out_ uint32_t& offset)
{
    size += sizeof(Internal::AllocationEntry);

    if (allocator.FreeOffset + size >= allocator.AllocationBlockSize + allocator.FirstAllocationOffset)
    {
        return E_OUTOFMEMORY;
    }

    BytePtr memoryRegionPtr(reinterpret_cast<byte*>(&allocator) - allocator.OffsetToAllocator);

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
        AllocationEntry* lastAllocationEntry =
            reinterpret_cast<AllocationEntry*>(memoryRegionPtr.Pointer + allocator.LastAllocatedOffset);

        lastAllocationEntry->NextEntryOffset = offset;
    }

    // Update current allocated entry.
    //
    AllocationEntry* allocationEntry = reinterpret_cast<AllocationEntry*>(memoryRegionPtr.Pointer + offset);
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
