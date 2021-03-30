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

    void Assign(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept;

    // Creates a new shared memory view.
    //
    _Must_inspect_result_
    HRESULT CreateNew(
        _In_z_ const char* sharedMemoryMapName,
        _In_ size_t memSize) noexcept;

    // Creates or opens a shared memory view.
    //
    _Must_inspect_result_
    HRESULT CreateOrOpen(
        _In_z_ const char* sharedMemoryMapName,
        _In_ size_t memSize) noexcept;

    // Opens already created shared memory view.
    //
    _Must_inspect_result_
    HRESULT OpenExisting(_In_z_ const char* sharedMemoryMapName) noexcept;

    // Opens already created shared memory view.
    //
    _Must_inspect_result_
    HRESULT OpenFromHandle(
        _In_ HANDLE hFile,
        _In_ size_t memSize);

    // Closes a shared memory handle.
    //
    void Close(_In_ bool cleanupOnClose = false);

    bool IsCreated() const;

private:
    _Must_inspect_result_
    HRESULT MapMemoryView(_In_ size_t memSize) noexcept;

public:
    BytePtr Buffer;
    size_t MemSize;

public:
    HANDLE m_hFile;
    HANDLE m_hMapFile;
    bool m_isCreated;
};
}
}
