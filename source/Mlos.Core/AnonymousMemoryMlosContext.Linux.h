//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: AnonymousMemoryMlosContext.Linux.h
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
// NAME: AnonymousMemoryMlosContextInitializer
//
// PURPOSE:
//  Implementation of an inter-process MlosContext based on anonymous shared memory.
//  Shared memory file descriptors are exchanged using Unix domain socket.
//
// NOTES:
//
class AnonymousMemoryMlosContext : public MlosContext
{
public:
    // Create with default arguments.
    //
    _Must_inspect_result_
    HRESULT static Create(_Inout_ AlignedInstance<AnonymousMemoryMlosContext>& mlosContextInstance);

    // Create.
    //
    _Must_inspect_result_
    HRESULT static Create(
        _Inout_ AlignedInstance<AnonymousMemoryMlosContext>& mlosContextInstance,
        _In_z_ const char* socketFolderPath,
        _In_ size_t sharedConfigMemorySize);

    AnonymousMemoryMlosContext(
        _In_ SharedMemoryRegionView<Internal::GlobalMemoryRegion>&& globalMemoryRegionView,
        _In_ SharedMemoryMapView&& controlChannelMemoryMapView,
        _In_ SharedMemoryMapView&& feedbackChannelMemoryMapView,
        _In_ SharedMemoryRegionView<Internal::SharedConfigMemoryRegion>&& sharedConfigMemoryRegionView,
        _In_ InterProcessSharedChannelPolicy&& controlChannelPolicy,
        _In_ InterProcessSharedChannelPolicy&& feedbackChannelPolicy,
        _In_ FileWatchEvent&& fileWatchEvent,
        _In_z_ char* socketFilePath) noexcept;

    AnonymousMemoryMlosContext(_In_ const AnonymousMemoryMlosContext&) = delete;

    AnonymousMemoryMlosContext& operator=(_In_ const AnonymousMemoryMlosContext&) = delete;

    ~AnonymousMemoryMlosContext();

private:
    _Must_inspect_result_
    HRESULT CreateSocketWatchFile();

    static void* HandleFdRequestsThreadProc(_In_ void* pParam);

    _Must_inspect_result_
    HRESULT HandleFdRequests();

    _Must_inspect_result_
    static HRESULT CreateOrOpenSharedMemory(
        _In_ FileDescriptorExchange& fileDescriptorExchange,
        _In_ MlosInternal::GlobalMemoryRegion& globalMemoryRegion,
        _In_ MlosInternal::MemoryRegionId memRegionId,
        _Inout_ MlosCore::SharedMemoryMapView& sharedMemoryMapView,
        _In_ const size_t memSize);

private:
    // Global shared memory region.
    //
    SharedMemoryRegionView<Internal::GlobalMemoryRegion> m_globalMemoryRegionView;

    // Shared memory for Telemetry and Control Channel.
    //
    SharedMemoryMapView m_controlChannelMemoryMapView;

    // Shared memory for Feedback Channel.
    //
    SharedMemoryMapView m_feedbackChannelMemoryMapView;

    // Shared memory for configs.
    //
    SharedMemoryRegionView<Internal::SharedConfigMemoryRegion> m_sharedConfigMemoryRegionView;

    // Channel policy for control channel.
    //
    InterProcessSharedChannelPolicy m_controlChannelPolicy;

    InterProcessSharedChannel m_controlChannel;

    // Channel policy for feedback channel.
    //
    InterProcessSharedChannel m_feedbackChannel;

    FileWatchEvent m_fileWatchEvent;

    ThreadHandle m_fdExchangeThread;

    char* m_socketFilePath;
};
}
}
