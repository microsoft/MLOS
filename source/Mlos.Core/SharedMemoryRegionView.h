//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedMemoryRegionView.h
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
class SharedMemoryRegionView : public SharedMemoryMapView
{
public:
    SharedMemoryRegionView() noexcept
    {}

    SharedMemoryRegionView(SharedMemoryRegionView<T>&& sharedMemoryRegionView) noexcept
      : SharedMemoryMapView(std::move(sharedMemoryRegionView))
    {}

    _Check_return_
    HRESULT CreateOrOpen(const char* const sharedMemoryMapName, size_t memSize) noexcept
    {
        HRESULT hr;
        hr = SharedMemoryMapView::CreateOrOpen(sharedMemoryMapName, memSize);
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

        return hr;
    }

    _Check_return_
    HRESULT Open(const char* const sharedMemoryMapName) noexcept
    {
        HRESULT hr;
        hr = SharedMemoryMapView::Open(sharedMemoryMapName);
        if (FAILED(hr))
        {
            return hr;
        }

        return hr;
    }

    T& MemoryRegion()
    {
        return *(reinterpret_cast<T*>(Buffer.Pointer));
    }

    template<typename TCodegenType>
    TCodegenType& GetCodegenObject(uint64_t offset)
    {
        return *reinterpret_cast<TCodegenType*>(Buffer.Pointer + offset);
    }

    T& InitializeMemoryRegion();
};
}
}
