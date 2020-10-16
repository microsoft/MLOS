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

#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Constructor.
//
SharedMemoryMapView::SharedMemoryMapView() noexcept
 :  MemSize(0),
    Buffer(nullptr),
    CleanupOnClose(false),
    m_fdSharedMemory(INVALID_FD_VALUE),
    m_sharedMemoryMapName(nullptr)
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
// NAME: SharedMemoryMapView::Constructor.
//
// PURPOSE:
//  Move constructor.
//
SharedMemoryMapView::SharedMemoryMapView(SharedMemoryMapView&& sharedMemoryMapView) noexcept :
    MemSize(std::exchange(sharedMemoryMapView.MemSize, 0)),
    Buffer(std::exchange(sharedMemoryMapView.Buffer, nullptr)),
    CleanupOnClose(std::exchange(sharedMemoryMapView.CleanupOnClose, 0)),
    m_fdSharedMemory(std::exchange(sharedMemoryMapView.m_fdSharedMemory, INVALID_FD_VALUE)),
    m_sharedMemoryMapName(std::exchange(sharedMemoryMapView.m_sharedMemoryMapName, nullptr))
{
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
HRESULT SharedMemoryMapView::CreateNew(const char* const sharedMemoryMapName, size_t memSize) noexcept
{
    Close();

    shm_unlink(sharedMemoryMapName);

    m_sharedMemoryMapName = strdup(sharedMemoryMapName);
    if (m_sharedMemoryMapName == nullptr)
    {
        return E_OUTOFMEMORY;
    }

    m_fdSharedMemory = shm_open(sharedMemoryMapName, O_EXCL | O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);

    return MapMemoryView(memSize);
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
HRESULT SharedMemoryMapView::CreateOrOpen(const char* const sharedMemoryMapName, size_t memSize) noexcept
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
HRESULT SharedMemoryMapView::OpenExisting(const char* const sharedMemoryMapName) noexcept
{
    Close();

    m_sharedMemoryMapName = strdup(sharedMemoryMapName);
    if (m_sharedMemoryMapName == nullptr)
    {
        return E_OUTOFMEMORY;
    }

    m_fdSharedMemory = shm_open(sharedMemoryMapName, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);
    if (m_fdSharedMemory == INVALID_FD_VALUE)
    {
        return HRESULT_FROM_ERRNO(errno);
    }

    return MapMemoryView(0 /* memSize */);
}

HRESULT SharedMemoryMapView::MapMemoryView(size_t memSize) noexcept
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
        void* pointer = mmap(0, memSize, PROT_READ | PROT_WRITE, MAP_SHARED, m_fdSharedMemory, 0);
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
void SharedMemoryMapView::Close()
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

        if (CleanupOnClose)
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

    CleanupOnClose = false;
}
}
}
