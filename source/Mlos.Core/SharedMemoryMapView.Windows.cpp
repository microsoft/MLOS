//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedMemoryMapView.Windows.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Constructor
//
SharedMemoryMapView::SharedMemoryMapView() noexcept
  : Buffer(nullptr),
    MemSize(0),
    m_hFile(INVALID_HANDLE_VALUE),
    m_hMapFile(nullptr),
    m_isCreated(false)
{
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Constructor.
//
// PURPOSE:
//  Move constructor.
//
SharedMemoryMapView::SharedMemoryMapView(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept
  : Buffer(std::exchange(sharedMemoryMapView.Buffer, nullptr)),
    MemSize(std::exchange(sharedMemoryMapView.MemSize, 0)),
    m_hFile(std::exchange(sharedMemoryMapView.m_hFile, INVALID_HANDLE_VALUE)),
    m_hMapFile(std::exchange(sharedMemoryMapView.m_hMapFile, nullptr)),
    m_isCreated(std::exchange(sharedMemoryMapView.m_isCreated, false))
{
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Destructor
//
SharedMemoryMapView::~SharedMemoryMapView()
{
    Close();
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Assign
//
// PURPOSE:
//  Assign method.
//
void SharedMemoryMapView::Assign(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept
{
    Buffer = std::exchange(sharedMemoryMapView.Buffer, nullptr);
    MemSize = std::exchange(sharedMemoryMapView.MemSize, 0);
    m_hFile = std::exchange(sharedMemoryMapView.m_hFile, INVALID_HANDLE_VALUE);
    m_hMapFile = std::exchange(sharedMemoryMapView.m_hMapFile, nullptr);
    m_isCreated = std::exchange(sharedMemoryMapView.m_isCreated, false);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::CreateNew
//
// PURPOSE:
//  Creates a new shared memory map view.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::CreateNew(
    _In_z_ const char* sharedMemoryMapName,
    _In_ size_t memSize) noexcept
{
    Close();

    PSECURITY_DESCRIPTOR pSecurityDescriptor = nullptr;

    HRESULT hr = Security::CreateDefaultSecurityDescriptor(pSecurityDescriptor);

    if (SUCCEEDED(hr))
    {
        SECURITY_ATTRIBUTES securityAttributes = { 0 };
        securityAttributes.nLength = sizeof(SECURITY_ATTRIBUTES);
        securityAttributes.bInheritHandle = false;
        securityAttributes.lpSecurityDescriptor = pSecurityDescriptor;

        m_hMapFile = CreateFileMappingA(
            INVALID_HANDLE_VALUE,   // use paging file
            &securityAttributes,    // security attributes
            PAGE_READWRITE,         // read/write access
            higher_uint32(memSize), // maximum object size (high-order DWORD)
            lower_uint32(memSize),  // maximum object size (low-order DWORD)
            sharedMemoryMapName);   // name of mapping object
        if (m_hMapFile == nullptr)
        {
            hr = HRESULT_FROM_WIN32(GetLastError());
        }

        LocalFree(pSecurityDescriptor);
    }

    if (SUCCEEDED(hr))
    {
        hr = Security::VerifyHandleOwner(m_hMapFile);
    }

    if (SUCCEEDED(hr))
    {
        hr = MapMemoryView(memSize);
    }

    if (SUCCEEDED(hr))
    {
        m_isCreated = true;
    }
    else
    {
        // If we fail, close all opened handles.
        //
        Close();
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::CreateOrOpen
//
// PURPOSE:
//  Creates or opens a shared memory view.
//
// RETURNS:
//  S_OK if created a new shared memory view.
//  S_FALSE if we open existing shared memory view.
//
// NOTES:
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::CreateOrOpen(
    _In_z_ const char* sharedMemoryMapName,
    _In_ size_t memSize) noexcept
{
    Close();

    // Try to open existing shared memory map.
    //
    HRESULT hr = OpenExisting(sharedMemoryMapName);

    if (SUCCEEDED(hr))
    {
        // Return S_FALSE, we opened existing shared memory view.
        //
        return S_FALSE;
    }

    return CreateNew(sharedMemoryMapName, memSize);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::OpenExisting
//
// PURPOSE:
//  Opens already created shared memory view.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::OpenExisting(_In_z_ const char* const sharedMemoryMapName) noexcept
{
    Close();

    HRESULT hr = S_OK;

    m_hMapFile = OpenFileMappingA(
        FILE_MAP_READ | FILE_MAP_WRITE, // read/write access
        FALSE,                          // inherit handle
        sharedMemoryMapName);           // name of mapping object
    if (m_hMapFile == nullptr)
    {
        hr = HRESULT_FROM_WIN32(GetLastError());
    }

    if (SUCCEEDED(hr))
    {
        hr = Security::VerifyHandleOwner(m_hMapFile);
    }

    if (SUCCEEDED(hr))
    {
        hr = MapMemoryView(0 /* memSize */);
    }

    if (FAILED(hr))
    {
        // If we fail, close all opened handles.
        //
        Close();
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::OpenFromHandle
//
// PURPOSE:
//  Opens shared mapping from the file handle.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::OpenFromHandle(
    _In_ HANDLE hFile,
    _In_ size_t memSize)
{
    Close();

    HRESULT hr = S_OK;

    m_hFile = hFile;
    m_isCreated = memSize != 0;

    if (memSize == 0)
    {
        // Get the map size from the file size.
        //
        LARGE_INTEGER queryMemSize = {};
        if (SUCCEEDED(hr))
        {
            if (!GetFileSizeEx(m_hFile, &queryMemSize))
            {
                hr = HRESULT_FROM_WIN32(GetLastError());
            }
        }

        if (SUCCEEDED(hr))
        {
            memSize = queryMemSize.QuadPart;
        }
    }

    if (SUCCEEDED(hr))
    {
        m_hMapFile = CreateFileMappingA(
            m_hFile,                // use paging file
            nullptr,                // security attributes
            PAGE_READWRITE,         // read/write access
            higher_uint32(memSize), // maximum object size (high-order DWORD)
            lower_uint32(memSize),  // maximum object size (low-order DWORD)
            nullptr);               // name of mapping object
        if (m_hMapFile == nullptr)
        {
            hr = HRESULT_FROM_WIN32(GetLastError());
        }
    }

    if (SUCCEEDED(hr))
    {
        hr = MapMemoryView(memSize);
    }

    if (FAILED(hr))
    {
        // If we fail, close all opened handles.
        //
        Close();
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::MapMemoryView
//
// PURPOSE:
//  Maps a view of a file mapping into the address space of a calling process.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//  If the size is not specified, function will query OS to obtain the size of the file mapping.
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::MapMemoryView(_In_ size_t memSize) noexcept
{
    HRESULT hr = S_OK;

    void* bufferPtr = MapViewOfFile(
        m_hMapFile,          // handle to map object
        FILE_MAP_ALL_ACCESS, // read/write permission
        0,
        0,
        memSize);
    if (bufferPtr == nullptr)
    {
        hr = HRESULT_FROM_WIN32(GetLastError());
    }

    if (SUCCEEDED(hr) && memSize == 0)
    {
        MEMORY_BASIC_INFORMATION memInfo = {};

        const SIZE_T memInfoResult = VirtualQueryEx(
            ::GetCurrentProcess(),
            bufferPtr,
            &memInfo,
            sizeof(memInfo));
        if (memInfoResult == 0)
        {
            hr = HRESULT_FROM_WIN32(GetLastError());
        }

        memSize = memInfo.RegionSize;
    }

    if (SUCCEEDED(hr))
    {
        Buffer = static_cast<byte*>(bufferPtr);
        MemSize = memSize;
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Close
//
// PURPOSE:
//  Closes a shared memory handle.
//
void SharedMemoryMapView::Close(_In_ bool cleanupOnClose)
{
    MLOS_UNUSED_ARG(cleanupOnClose);

    m_isCreated = false;

    UnmapViewOfFile(Buffer.Pointer);
    Buffer.Pointer = nullptr;

    CloseHandle(m_hMapFile);
    m_hMapFile = nullptr;

    CloseHandle(m_hFile);
    m_hFile = INVALID_HANDLE_VALUE;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::IsCreated
//
// PURPOSE:
//  Returns true if shared memory was created.
//
bool SharedMemoryMapView::IsCreated() const
{
    return m_isCreated;
}
}
}
