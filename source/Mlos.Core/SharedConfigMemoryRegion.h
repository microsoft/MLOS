//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfigMemoryRegion.h
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
HRESULT AllocateInSharedConfigMemoryRegion(
    SharedConfigMemoryRegion& memoryRegion,
    uint64_t size,
    _Out_ uint32_t& offset);
}
}
}
