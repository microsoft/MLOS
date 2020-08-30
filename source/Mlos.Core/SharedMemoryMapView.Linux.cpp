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
#include <unistd.h>
#include <fcntl.h>

using namespace Mlos::Core;

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Constructor.
//
SharedMemoryMapView::SharedMemoryMapView() noexcept
 :  MemSize(0),
    m_fdSharedMemory(INVALID_FD_VALUE),
    Buffer(nullptr)
{
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Constructor.
//
// PURPOSE:
//  Move constructor.
//
SharedMemoryMapView::SharedMemoryMapView(SharedMemoryMapView&& sharedMemoryMapView) noexcept :
    MemSize(std::exchange(sharedMemoryMapView.MemSize, 0)),
    m_fdSharedMemory(std::exchange(sharedMemoryMapView.m_fdSharedMemory, INVALID_FD_VALUE)),
    Buffer(std::exchange(sharedMemoryMapView.Buffer, nullptr))
{
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Create
//
// PURPOSE:
//  Creates a new shared memory map view.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
HRESULT SharedMemoryMapView::Create(const char* const sharedMemoryMapName, size_t memSize) noexcept
{
    shm_unlink(sharedMemoryMapName);

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
    m_fdSharedMemory = shm_open(sharedMemoryMapName, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);

    return MapMemoryView(memSize);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Open
//
// PURPOSE:
//  Opens already created shared memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
HRESULT SharedMemoryMapView::Open(const char* const sharedMemoryMapName) noexcept
{
    m_fdSharedMemory = shm_open(sharedMemoryMapName, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);

    return MapMemoryView(0 /* memSize */);
}

HRESULT SharedMemoryMapView::MapMemoryView(size_t memSize) noexcept
{
    if (m_fdSharedMemory == -1)
    {
        return HRESULT_FROM_ERRNO(errno);
    }

    if (ftruncate(m_fdSharedMemory, memSize) == -1)
    {
        return HRESULT_FROM_ERRNO(errno);
    }

    Buffer = mmap(0, memSize, PROT_READ | PROT_WRITE, MAP_SHARED, m_fdSharedMemory, 0);

    //#handle failure
    MemSize = memSize;

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Destructor
//
SharedMemoryMapView::~SharedMemoryMapView()
{
    if (m_fdSharedMemory != INVALID_FD_VALUE)
    {
        close(m_fdSharedMemory);
    }
}
