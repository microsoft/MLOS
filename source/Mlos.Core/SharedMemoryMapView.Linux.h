#pragma once

namespace Mlos
{
namespace Core
{

class SharedMemoryMapView
{
public:
    SharedMemoryMapView() noexcept;

    SharedMemoryMapView(SharedMemoryMapView&& SharedMemoryMapView) noexcept;

    _Check_return_
    HRESULT CreateOrOpen(const char* const sharedMemoryMapName, size_t memSize) noexcept;

    _Check_return_
    HRESULT Open(const char* const sharedMemoryMapName) noexcept;

    ~SharedMemoryMapView();

private:
    _Check_return_
    HRESULT MapMemoryView(size_t memSize) noexcept;

public:
    size_t MemSize;
    BytePtr Buffer;

private:
    // HANDLE m_hMapFile;
};

}
}