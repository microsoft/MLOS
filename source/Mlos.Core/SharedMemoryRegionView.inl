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
template<typename T>
HRESULT SharedMemoryRegionView<T>::CreateNew(const char* const sharedMemoryMapName, size_t memSize) noexcept
{
    HRESULT hr = SharedMemoryMapView::CreateNew(sharedMemoryMapName, memSize);
    if (FAILED(hr))
    {
        return hr;
    }

    InitializeMemoryRegionView();

    return hr;
}

template<typename T>
HRESULT SharedMemoryRegionView<T>::CreateOrOpen(const char* const sharedMemoryMapName, size_t memSize) noexcept
{
    HRESULT hr = SharedMemoryMapView::CreateOrOpen(sharedMemoryMapName, memSize);
    if (FAILED(hr))
    {
        return hr;
    }

    if (hr == S_FALSE)
    {
        // We opened a existing shared memory view. Do not initialize it.
        //
        return hr;
    }

    InitializeMemoryRegionView();

    return hr;
}

template<typename T>
HRESULT SharedMemoryRegionView<T>::OpenExisting(const char* const sharedMemoryMapName) noexcept
{
    HRESULT hr = SharedMemoryMapView::OpenExisting(sharedMemoryMapName);

    return hr;
}

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
        memoryRegion.MemoryHeader.MemoryRegionSize = MemSize;
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
