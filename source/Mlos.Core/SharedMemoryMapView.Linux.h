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

    SharedMemoryMapView(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept;

    ~SharedMemoryMapView();

    void Assign(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept;

    // Creates an anonymous shared memory view.
    //
    _Must_inspect_result_
    HRESULT CreateAnonymous(_In_ size_t memSize) noexcept;

    // Creates a shared memory view.
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

    _Must_inspect_result_
    HRESULT OpenExistingFromFileDescriptor(
        _In_z_ int sharedMemoryFd,
        _In_ size_t memSize) noexcept;

    // Opens already created shared memory view.
    //
    _Must_inspect_result_
    HRESULT OpenExisting(_In_z_ const char* const sharedMemoryMapName) noexcept;

    // Closes a shared memory view.
    //
    void Close();

    // Gets a shared memory file descriptor.
    //
    int GetFileDescriptor() const;

private:
    _Must_inspect_result_
    HRESULT MapMemoryView(_In_ size_t memSize) noexcept;

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
