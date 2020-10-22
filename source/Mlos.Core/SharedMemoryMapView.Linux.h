//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedMemoryMapView.Linux.h
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
class SharedMemoryMapView
{
public:
    SharedMemoryMapView() noexcept;

    SharedMemoryMapView(SharedMemoryMapView&& sharedMemoryMapView) noexcept;

    ~SharedMemoryMapView();

    // Creates a shared memory view.
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

    // Closes a shared memory view.
    //
    void Close();

private:
    _Check_return_
    HRESULT MapMemoryView(size_t memSize) noexcept;

public:
    size_t MemSize;
    BytePtr Buffer;

    // Indicates if we should cleanup OS resources when closing the shared memory map view.
    //
    bool CleanupOnClose;

private:
    int m_fdSharedMemory;
    char* m_sharedMemoryMapName;
};

}
}
