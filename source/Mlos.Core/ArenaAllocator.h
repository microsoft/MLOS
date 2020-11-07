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
_Check_return_
HRESULT InitializeArenaAllocator(
    ArenaAllocator& allocator,
    MemoryRegion& memoryRegion,
    int32_t allocationBlockOffset);

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
_Check_return_
HRESULT AllocateInMemoryRegion(
    ArenaAllocator& allocator,
    uint64_t size,
    _Out_ uint32_t& offset);
}
}
}
