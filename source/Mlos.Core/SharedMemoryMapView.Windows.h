//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedMemoryMapView.Windows.h
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
// NAME: SharedMemoryMapView
//
// PURPOSE:
//  Class is used to manage a named file mapping object.
//
// NOTES:
//  Windows implementation.
//
class SharedMemoryMapView
{
public:
    SharedMemoryMapView() noexcept;

    SharedMemoryMapView(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept;

    ~SharedMemoryMapView();

    // Creates a new shared memory view.
    //
    _Check_return_
    HRESULT CreateNew(
        _In_z_ const char* const sharedMemoryMapName,
        _In_ size_t memSize) noexcept;

    // Creates or opens a shared memory view.
    //
    _Check_return_
    HRESULT CreateOrOpen(
        _In_z_ const char* const sharedMemoryMapName,
        _In_ size_t memSize) noexcept;

    // Opens already created shared memory view.
    //
    _Check_return_
    HRESULT OpenExisting(_In_z_ const char* const sharedMemoryMapName) noexcept;

    // Closes a shared memory handle.
    //
    void Close();

private:
    _Check_return_
    HRESULT MapMemoryView(_In_ size_t memSize) noexcept;

public:
    size_t MemSize;
    BytePtr Buffer;

    // Indicates if we should cleanup OS resources when closing the shared memory map view.
    // No-op on Windows.
    //
    bool CleanupOnClose;

private:
    HANDLE m_hMapFile;
};
}
}
