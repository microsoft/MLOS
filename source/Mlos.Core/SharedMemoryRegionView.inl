//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedMemoryRegionView.inl
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
//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView<T>::InitializeMemoryRegionView
//
// PURPOSE:
//  Initializes a new memory region.
//
// NOTES:
//
template<typename T>
void SharedMemoryRegionView<T>::InitializeMemoryRegionView()
{
    // Initialize the memory region header.
    //
    {
        T& memoryRegion = MemoryRegion();

        memoryRegion.MemoryHeader.Signature = 0x67676767;
        memoryRegion.MemoryHeader.MemoryRegionSize = m_sharedMemoryMapView.MemSize;
        memoryRegion.MemoryHeader.MemoryRegionCodeTypeIndex = TypeMetadataInfo::CodegenTypeIndex<T>();
    }

    // Initialize the memory region.
    //
    {
        T& memoryRegion = InitializeMemoryRegion();
        (void)memoryRegion;
    }
}
}
}
