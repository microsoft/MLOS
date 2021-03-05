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

    // Creates an anonymous shared memory view (no file backing).
    //
    _Must_inspect_result_
    HRESULT CreateAnonymous(
        _In_z_ const char* sharedMemoryMapName,
        _In_ size_t memSize) noexcept;

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

    // Opens a shared memory map from the file descriptor.
    //
    _Must_inspect_result_
    HRESULT OpenExistingFromFileDescriptor(
        _In_z_ const char* sharedMemoryMapName,
        _In_ int32_t sharedMemoryFd) noexcept;

    // Opens already created shared memory view.
    //
    _Must_inspect_result_
    HRESULT OpenExisting(_In_z_ const char* sharedMemoryMapName) noexcept;

    // Closes a shared memory view.
    //
    void Close(_In_ bool cleanupOnClose = false);

    const char* GetSharedMemoryMapName() const;

    // Gets a shared memory file descriptor.
    //
    int32_t GetFileDescriptor() const;

    bool IsCreated() const;

private:
    _Must_inspect_result_
    HRESULT MapMemoryView(_In_ size_t memSize) noexcept;

public:
    size_t MemSize;
    BytePtr Buffer;

private:
    int32_t m_fdSharedMemory;
    char* m_sharedMemoryMapName;
    bool m_isCreated;
};
}
}
