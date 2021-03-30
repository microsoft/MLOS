//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedMemoryMapView.Linux.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

#include <linux/memfd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <fcntl.h>
#include <unistd.h>

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: memfd_create
//
// PURPOSE:
//  Creates an anonymous file.
//
// RETURNS:
//  Returns a file descriptor that refers to anonymous file.
//
// NOTES:
//  Use syscall as memfd_create function is not always defined in the system's version of libc (memfd_create was added in 2.27 for glibc).
//
int memfd_create(const char* name, unsigned int flags)
{
    return syscall(SYS_memfd_create, name, flags);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Constructor
//
SharedMemoryMapView::SharedMemoryMapView() noexcept
 :  MemSize(0),
    Buffer(nullptr),
    m_fdSharedMemory(INVALID_FD_VALUE),
    m_sharedMemoryMapName(nullptr),
    m_isCreated(false)
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
// NAME: SharedMemoryMapView::Constructor
//
// PURPOSE:
//  Move constructor.
//
SharedMemoryMapView::SharedMemoryMapView(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept :
    MemSize(std::exchange(sharedMemoryMapView.MemSize, 0)),
    Buffer(std::exchange(sharedMemoryMapView.Buffer, nullptr)),
    m_fdSharedMemory(std::exchange(sharedMemoryMapView.m_fdSharedMemory, INVALID_FD_VALUE)),
    m_sharedMemoryMapName(std::exchange(sharedMemoryMapView.m_sharedMemoryMapName, nullptr)),
    m_isCreated(std::exchange(sharedMemoryMapView.m_isCreated, false))
{
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Assign
//
// PURPOSE:
//  Assign method.
//
// RETURNS:
//
// NOTES:
//
void SharedMemoryMapView::Assign(_In_ SharedMemoryMapView&& sharedMemoryMapView) noexcept
{
    MemSize = std::exchange(sharedMemoryMapView.MemSize, 0);
    Buffer = std::exchange(sharedMemoryMapView.Buffer, nullptr);
    m_fdSharedMemory = std::exchange(sharedMemoryMapView.m_fdSharedMemory, INVALID_FD_VALUE);
    m_sharedMemoryMapName = std::exchange(sharedMemoryMapView.m_sharedMemoryMapName, nullptr);
    m_isCreated = std::exchange(sharedMemoryMapView.m_isCreated, false);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::CreateAnonymous
//
// PURPOSE:
//  Creates an anonymous shared memory view (no file backing).
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//  SharedMemoryMapName is used as an identifier.
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::CreateAnonymous(
    _In_z_ const char* sharedMemoryMapName,
    _In_ size_t memSize) noexcept
{
    Close();

    m_sharedMemoryMapName = strdup(sharedMemoryMapName);
    if (m_sharedMemoryMapName == nullptr)
    {
        return E_OUTOFMEMORY;
    }

    m_fdSharedMemory = memfd_create("mlos", MFD_CLOEXEC);
    HRESULT hr = MapMemoryView(memSize);

    if (SUCCEEDED(hr))
    {
        m_isCreated = true;
    }

    return hr;
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
    _In_z_ const char* const sharedMemoryMapName,
    _In_ size_t memSize) noexcept
{
    Close();

    shm_unlink(sharedMemoryMapName);

    m_sharedMemoryMapName = strdup(sharedMemoryMapName);
    if (m_sharedMemoryMapName == nullptr)
    {
        return E_OUTOFMEMORY;
    }

    m_fdSharedMemory = shm_open(sharedMemoryMapName, O_EXCL | O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);

    HRESULT hr = MapMemoryView(memSize);

    if (SUCCEEDED(hr))
    {
        m_isCreated = true;
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::CreateOrOpen
//
// PURPOSE:
//  Creates or opens a shared memory map view.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::CreateOrOpen(
    _In_z_ const char* sharedMemoryMapName,
    _In_ size_t memSize) noexcept
{
    Close();

    m_sharedMemoryMapName = strdup(sharedMemoryMapName);
    if (m_sharedMemoryMapName == nullptr)
    {
        return E_OUTOFMEMORY;
    }

    m_fdSharedMemory = shm_open(sharedMemoryMapName, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);

    return MapMemoryView(memSize);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::OpenExisting
//
// PURPOSE:
//  Opens already created shared memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::OpenExisting(_In_z_ const char* sharedMemoryMapName) noexcept
{
    Close();

    m_sharedMemoryMapName = strdup(sharedMemoryMapName);
    if (m_sharedMemoryMapName == nullptr)
    {
        return E_OUTOFMEMORY;
    }

    m_fdSharedMemory = shm_open(sharedMemoryMapName, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);

    return MapMemoryView(0 /* memSize */);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::OpenExistingFromFileDescriptor
//
// PURPOSE:
//  Opens already created shared memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::OpenExistingFromFileDescriptor(
    _In_z_ const char* sharedMemoryMapName,
    _In_ int32_t sharedMemoryFd) noexcept
{
    Close();

    m_sharedMemoryMapName = strdup(sharedMemoryMapName);
    if (m_sharedMemoryMapName == nullptr)
    {
        return E_OUTOFMEMORY;
    }

    m_fdSharedMemory = sharedMemoryFd;

    return MapMemoryView(0 /* memSize */);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::MapMemoryView
//
// PURPOSE:
//  Creates a memory map.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
_Must_inspect_result_
HRESULT SharedMemoryMapView::MapMemoryView(_In_ size_t memSize) noexcept
{
    HRESULT hr = S_OK;

    if (m_fdSharedMemory == INVALID_FD_VALUE)
    {
        hr = HRESULT_FROM_ERRNO(errno);
    }

    if (SUCCEEDED(hr))
    {
        if (memSize == 0)
        {
            // Obtain the size of the shared map.
            //
            struct stat statBuffer = { };
            if (fstat(m_fdSharedMemory, &statBuffer) != -1)
            {
                memSize = statBuffer.st_size;
            }
            else
            {
                hr = HRESULT_FROM_ERRNO(errno);
            }
        }
    }

    if (SUCCEEDED(hr))
    {
        if (ftruncate(m_fdSharedMemory, memSize) == -1)
        {
            hr = HRESULT_FROM_ERRNO(errno);
        }
    }

    if (SUCCEEDED(hr))
    {
        void* pointer = mmap(nullptr, memSize, PROT_READ | PROT_WRITE, MAP_SHARED, m_fdSharedMemory, 0);
        if (pointer != MAP_FAILED)
        {
            Buffer.Pointer = reinterpret_cast<byte*>(pointer);
            MemSize = memSize;
        }
        else
        {
            hr = HRESULT_FROM_ERRNO(errno);
        }
    }

    if (FAILED(hr))
    {
        Close();
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Close
//
// PURPOSE:
//  Closes a shared memory view.
//
void SharedMemoryMapView::Close(_In_ bool cleanupOnClose)
{
    if (Buffer.Pointer != nullptr)
    {
        munmap(Buffer.Pointer, MemSize);
        Buffer = nullptr;

        MemSize = 0;
    }

    if (m_fdSharedMemory != INVALID_FD_VALUE)
    {
        close(m_fdSharedMemory);
        m_fdSharedMemory = INVALID_FD_VALUE;

        if (cleanupOnClose)
        {
            if (m_sharedMemoryMapName != nullptr)
            {
                shm_unlink(m_sharedMemoryMapName);
            }
        }
    }

    if (m_sharedMemoryMapName != nullptr)
    {
        free(m_sharedMemoryMapName);
        m_sharedMemoryMapName = nullptr;
    }
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::GetSharedMemoryMapName
//
// PURPOSE:
//  Gets a shared memory map name.
//
const char* SharedMemoryMapView::GetSharedMemoryMapName() const
{
    return m_sharedMemoryMapName;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::GetFileDescriptor
//
// PURPOSE:
//  Gets a shared memory file descriptor.
//
int32_t SharedMemoryMapView::GetFileDescriptor() const
{
    return m_fdSharedMemory;
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
