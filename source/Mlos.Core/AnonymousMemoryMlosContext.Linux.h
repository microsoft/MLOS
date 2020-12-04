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
//  Helper class used to initialize AnonymousMemoryMlosContext.
//
// NOTES:
//
class AnonymousMemoryMlosContextInitializer
{
public:
    AnonymousMemoryMlosContextInitializer() {}

    _Must_inspect_result_
    HRESULT Initialize();

    AnonymousMemoryMlosContextInitializer(_In_ AnonymousMemoryMlosContextInitializer&& initializer) noexcept;

    AnonymousMemoryMlosContextInitializer(const AnonymousMemoryMlosContextInitializer&) = delete;

    AnonymousMemoryMlosContextInitializer& operator=(const AnonymousMemoryMlosContextInitializer&) = delete;

private:
    template<typename TSharedMemoryView>
    _Must_inspect_result_
    HRESULT CreateAnonymousSharedMemory(
            _In_ FileDescriptorExchange& fileDescriptorExchange,
            _Inout_ TSharedMemoryView& sharedMemory,
            _In_ Internal::MemoryRegionId memoryRegionId,
            _In_ std::size_t sharedMemorySize);

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

    // Channel policy for feedback channel.
    //
    InterProcessSharedChannelPolicy m_feedbackChannelPolicy;

    friend class AnonymousMemoryMlosContext;
};

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
    typedef AnonymousMemoryMlosContextInitializer InitializerType;

    AnonymousMemoryMlosContext(_In_ AnonymousMemoryMlosContextInitializer&&) noexcept;

    ~AnonymousMemoryMlosContext();

    _Must_inspect_result_
    HRESULT HandleFdRequests();

private:
    AnonymousMemoryMlosContextInitializer m_contextInitializer;

    InterProcessSharedChannel m_controlChannel;

    InterProcessSharedChannel m_feedbackChannel;

    NamedEvent m_controlChannelNamedEvent;

    NamedEvent m_feedbackChannelNamedEvent;
};

//----------------------------------------------------------------------------
// NAME: MlosContextFactory<AnonymousMemoryMlosContext>
//
// PURPOSE:
//  Template specialization of MlosContextFactory.
//
// NOTES:
//
template<>
_Must_inspect_result_
HRESULT MlosContextFactory<AnonymousMemoryMlosContext>::Create();
}
}
