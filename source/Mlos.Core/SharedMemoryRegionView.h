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
class SharedMemoryRegionView
{
public:
    SharedMemoryRegionView() noexcept = default;

    SharedMemoryRegionView(_In_ SharedMemoryRegionView<T>&& sharedMemoryRegionView) noexcept
      : m_sharedMemoryMapView(std::move(sharedMemoryRegionView.m_sharedMemoryMapView))
    {}

    SharedMemoryRegionView(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept
      : m_sharedMemoryMapView(std::move(sharedMemoryMapView))
    {
        if (m_sharedMemoryMapView.IsCreated())
        {
            InitializeMemoryRegionView();
        }
    }

    void Assign(_In_ SharedMemoryRegionView<T>&& sharedMemoryRegionView) noexcept
    {
        m_sharedMemoryMapView.Assign(std::move(sharedMemoryRegionView.m_sharedMemoryMapView));
    }

    T& MemoryRegion()
    {
        return *(reinterpret_cast<T*>(m_sharedMemoryMapView.Buffer.Pointer));
    }

    template<typename TCodegenType>
    TCodegenType& GetCodegenObject(_In_ uint64_t offset)
    {
        return *reinterpret_cast<TCodegenType*>(m_sharedMemoryMapView.Buffer.Pointer + offset);
    }

    // Gets a value that indicates whether the buffer is invalid.
    //
    bool IsInvalid() const
    {
        return m_sharedMemoryMapView.Buffer.Pointer == nullptr;
    }

    const SharedMemoryMapView& MapView() const
    {
        return m_sharedMemoryMapView;
    }

    void Close(bool cleanupOnClose = false)
    {
        m_sharedMemoryMapView.Close(cleanupOnClose);
    }

private:
    void InitializeMemoryRegionView();

    T& InitializeMemoryRegion();

    SharedMemoryMapView m_sharedMemoryMapView;
};
}
}
