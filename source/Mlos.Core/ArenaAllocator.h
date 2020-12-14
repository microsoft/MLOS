//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: ArenaAllocator.h
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
namespace Internal
{
//----------------------------------------------------------------------------
// NAME: InitializeArenaAllocator
//
// PURPOSE:
//  Initializes the arena allocator stored in the memory region.
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
    _In_ int32_t memoryRegionHeaderSize);

//----------------------------------------------------------------------------
// NAME: AllocateInMemoryRegion
//
// PURPOSE:
//  Allocates the memory in the shared memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//  Incremental allocator. Not thread safe.
//
_Must_inspect_result_
HRESULT AllocateInMemoryRegion(
    _Inout_ ArenaAllocator& allocator,
    _In_ uint64_t size,
    _Out_ uint32_t& offset);
}
}
}
