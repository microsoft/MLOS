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
_Must_inspect_result_
HRESULT InitializeArenaAllocator(
    _Inout_ ArenaAllocator& allocator,
    _Inout_ MemoryRegion& memoryRegion,
    _In_ int32_t memoryRegionHeaderSize)
{
    allocator.OffsetToAllocator = static_cast<int32_t>(BytePtr(&allocator).Pointer - BytePtr(&memoryRegion).Pointer);

    allocator.EndOffset = static_cast<uint32_t>(memoryRegion.MemoryRegionSize);

    allocator.FreeOffset = static_cast<uint32_t>(align<ArenaAllocator::AllocationAlignment>(memoryRegionHeaderSize));
    allocator.AllocationCount = 0;
    allocator.LastOffset = 0;

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
_Must_inspect_result_
HRESULT AllocateInMemoryRegion(
    _Inout_ ArenaAllocator& allocator,
    _In_ uint64_t size,
    _Out_ uint32_t& offset)
{
    size += sizeof(Internal::AllocationEntry);

    if (allocator.FreeOffset + size >= allocator.EndOffset)
    {
        return E_OUTOFMEMORY;
    }

    const BytePtr memoryRegionPtr(reinterpret_cast<byte*>(&allocator) - allocator.OffsetToAllocator);

    // Update the address.
    //
    offset = allocator.FreeOffset;

    // Update memory region properties.
    //
    allocator.FreeOffset += static_cast<uint32_t>(align<ArenaAllocator::AllocationAlignment>(size));
    allocator.AllocationCount++;

    // Update last allocated entry.
    //
    if (allocator.LastOffset != 0)
    {
        AllocationEntry* lastAllocationEntry =
            reinterpret_cast<AllocationEntry*>(memoryRegionPtr.Pointer + allocator.LastOffset);

        lastAllocationEntry->NextEntryOffset = offset;
    }

    // Update current allocated entry.
    //
    AllocationEntry* allocationEntry = reinterpret_cast<AllocationEntry*>(memoryRegionPtr.Pointer + offset);
    allocationEntry->PrevEntryOffset = allocator.LastOffset;

    allocator.LastOffset = offset;

    // Skip the allocation entry.
    //
    offset += sizeof(Internal::AllocationEntry);

    return S_OK;
}
}
}
}
