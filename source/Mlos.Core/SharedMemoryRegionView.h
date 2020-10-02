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

    // Opens already created shared memory view.
    //
    _Check_return_
    HRESULT CreateNew(const char* const sharedMemoryMapName, size_t memSize) noexcept;

    // Creates or opens a shared memory view.
    //
    _Check_return_
    HRESULT CreateOrOpen(const char* const sharedMemoryMapName, size_t memSize) noexcept;

    // Opens already created shared memory view.
    //
    _Check_return_
    HRESULT OpenExisting(const char* const sharedMemoryMapName) noexcept;

    T& MemoryRegion()
    {
        return *(reinterpret_cast<T*>(Buffer.Pointer));
    }

    template<typename TCodegenType>
    TCodegenType& GetCodegenObject(uint64_t offset)
    {
        return *reinterpret_cast<TCodegenType*>(Buffer.Pointer + offset);
    }

private:
    void InitializeMemoryRegionView();

    T& InitializeMemoryRegion();
};
}
}
