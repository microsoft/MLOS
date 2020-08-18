#include "Mlos.Core.h"

using namespace Mlos::Core;

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Constructor.
//
SharedMemoryMapView::SharedMemoryMapView() noexcept
 :  MemSize(0),
    // m_hMapFile(INVALID_HANDLE_VALUE),
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
    // m_hMapFile(std::exchange(sharedMemoryMapView.m_hMapFile, INVALID_HANDLE_VALUE)),
    Buffer(std::exchange(sharedMemoryMapView.Buffer, nullptr))
{
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Create
//
// PURPOSE:
//  Creates or opens a shared memory map view.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//  LinuxHE does not allow creating a global shared memory map.
//  Therefore we assume the mapping has been already created by the Mlos.Agent.
//
HRESULT SharedMemoryMapView::CreateOrOpen(const char* const sharedMemoryMapName, size_t memSize) noexcept
{
    return MapMemoryView(memSize);
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Open
//
// PURPOSE:
//  Open already created shared memory region.
//
// RETURNS:
//  HRESULT.
//
// NOTES:
//
HRESULT SharedMemoryMapView::Open(const char* const sharedMemoryMapName) noexcept
{
    return MapMemoryView(0 /* memSize */);
}

HRESULT SharedMemoryMapView::MapMemoryView(size_t memSize) noexcept
{
    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: SharedMemoryMapView::Destructor
//
SharedMemoryMapView::~SharedMemoryMapView()
{
}
