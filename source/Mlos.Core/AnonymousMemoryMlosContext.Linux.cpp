//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: AnonymousMemoryMlosContext.Linux.cpp
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#include "Mlos.Core.h"

#include <chrono>
#include <thread>

namespace Mlos
{
namespace Core
{
// File exchange Unix domain socket name.
//
const char* const FdUnitDomainSocketName = "/tmp/mlos.sock";

// Synchronization semaphore names.
//
const char* const FdExchangeSemaphoreName = "mlos_fd_exchange";
const char* const ControlChannelSemaphoreName = "mlos_control_channel_event";
const char* const FeedbackChannelSemaphoreName = "mlos_feedback_channel_event";

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContext::HandleFdRequests
//
// PURPOSE:
//  Function is responsible for sending the shared memory file descriptors.
//  Once the agents starts, it opens a unix domain socket and signals the fd exchange semaphore.
//  Then the function sends all file descriptors from the mlos context.
//
// NOTES:
//
_Must_inspect_result_
HRESULT AnonymousMemoryMlosContext::HandleFdRequests()
{
    NamedEvent fdExchangeNamedEvent;

    // Open an event used by the agent to signal when it is ready to get the file descriptors.
    //
    HRESULT hr = fdExchangeNamedEvent.CreateOrOpen(FdExchangeSemaphoreName);
    if (FAILED(hr))
    {
        // Failed to create waiting event.
        //
        return hr;
    }

    // Request loop.
    //
    while (true)
    {
        // Wait fot the agent when it is ready to get the file descriptors.
        //
        hr = fdExchangeNamedEvent.Wait();
        if (FAILED(hr))
        {
            // The wait failed.
            //
            break;
        }

        // Send the shared memory file descriptors to the agent.
        //
        const char* socketName = FdUnitDomainSocketName;
        FileDescriptorExchange fileDescriptorExchange;
        hr = fileDescriptorExchange.Connect(socketName);
        if (FAILED(hr))
        {
            // Failed to connect.
            //
            continue;
        }

        if SUCCEEDED(hr)
        {
            Internal::MemoryRegionId memoryRegionId = {};
            memoryRegionId.Type = Internal::MemoryRegionType::Global;

            hr = fileDescriptorExchange.SendFileDescriptor(
                    memoryRegionId,
                    m_contextInitializer.m_globalMemoryRegionView.GetFileDescriptor(),
                    m_contextInitializer.m_globalMemoryRegionView.MemSize);
        }

        if SUCCEEDED(hr)
        {
            Internal::MemoryRegionId memoryRegionId = {};
            memoryRegionId.Type = Internal::MemoryRegionType::ControlChannel;

            hr = fileDescriptorExchange.SendFileDescriptor(
                    memoryRegionId,
                    m_contextInitializer.m_controlChannelMemoryMapView.GetFileDescriptor(),
                    m_contextInitializer.m_controlChannelMemoryMapView.MemSize);
        }

        if SUCCEEDED(hr)
        {
            Internal::MemoryRegionId memoryRegionId = {};
            memoryRegionId.Type = Internal::MemoryRegionType::FeedbackChannel;

            hr = fileDescriptorExchange.SendFileDescriptor(
                    memoryRegionId,
                    m_contextInitializer.m_feedbackChannelMemoryMapView.GetFileDescriptor(),
                    m_contextInitializer.m_feedbackChannelMemoryMapView.MemSize);
        }

        if SUCCEEDED(hr)
        {
            Internal::MemoryRegionId memoryRegionId = {};
            memoryRegionId.Type = Internal::MemoryRegionType::SharedConfig;

            hr = fileDescriptorExchange.SendFileDescriptor(
                    memoryRegionId,
                    m_sharedConfigManager.m_sharedConfigMemoryRegionView.GetFileDescriptor(),
                    m_sharedConfigManager.m_sharedConfigMemoryRegionView.MemSize);
        }
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContextInitializer::Constructor.
//
// PURPOSE:
//  Move constructor.
//
// NOTES:
//
AnonymousMemoryMlosContextInitializer::AnonymousMemoryMlosContextInitializer(_In_ AnonymousMemoryMlosContextInitializer&& initializer) noexcept
  : m_globalMemoryRegionView(std::move(initializer.m_globalMemoryRegionView)),
    m_controlChannelMemoryMapView(std::move(initializer.m_controlChannelMemoryMapView)),
    m_feedbackChannelMemoryMapView(std::move(initializer.m_feedbackChannelMemoryMapView)),
    m_sharedConfigMemoryRegionView(std::move(initializer.m_sharedConfigMemoryRegionView)),
    m_controlChannelPolicy(std::move(initializer.m_controlChannelPolicy)),
    m_feedbackChannelPolicy(std::move(initializer.m_feedbackChannelPolicy))
{
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContextInitializer::Initialize
//
// PURPOSE:
//  Creates AnonymousMemoryMlosContext using anonymous shared memory region.
//
// NOTES:
//
_Must_inspect_result_
HRESULT AnonymousMemoryMlosContextInitializer::Initialize()
{
    const size_t SharedMemorySize = 65536;
    const char* socketName = FdUnitDomainSocketName;

    // Try to connect to the Mlos.Agent Unix domain socket.
    // If the agent is unavailable and we fail to connect,
    // we will send the file mappings after the agent becomes available
    // (AnonymousMemoryMlosContext::HandleFdRequests).
    //
    FileDescriptorExchange fileDescriptorExchange;
    HRESULT hr = fileDescriptorExchange.Connect(socketName);
    MLOS_IGNORE_HR(hr);

    {
        // Create global shared memory.
        //
        Internal::MemoryRegionId memoryRegionId = {};
        memoryRegionId.Type = Internal::MemoryRegionType::Global;

        hr = CreateAnonymousSharedMemory(
                fileDescriptorExchange,
                m_globalMemoryRegionView,
                memoryRegionId,
                SharedMemorySize);

        // Increase the usage counter.
        //
        Internal::GlobalMemoryRegion& globalMemoryRegion = m_globalMemoryRegionView.MemoryRegion();
        globalMemoryRegion.AttachedProcessesCount.fetch_add(1);
    }

    // Create control channel shared memory.
    //
    if (SUCCEEDED(hr))
    {
        Internal::MemoryRegionId memoryRegionId = {};
        memoryRegionId.Type = Internal::MemoryRegionType::ControlChannel;

        hr = CreateAnonymousSharedMemory(
                fileDescriptorExchange,
                m_controlChannelMemoryMapView,
                memoryRegionId,
                SharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        Internal::MemoryRegionId memoryRegionId = {};
        memoryRegionId.Type = Internal::MemoryRegionType::FeedbackChannel;

        hr = CreateAnonymousSharedMemory(
                fileDescriptorExchange,
                m_feedbackChannelMemoryMapView,
                memoryRegionId,
                SharedMemorySize);
    }

    // Create shared config memory.
    //
    if (SUCCEEDED(hr))
    {
        Internal::MemoryRegionId memoryRegionId = {};
        memoryRegionId.Type = Internal::MemoryRegionType::SharedConfig;

        hr = CreateAnonymousSharedMemory(
                fileDescriptorExchange,
                m_sharedConfigMemoryRegionView,
                memoryRegionId,
                SharedMemorySize);
    }

    // Create synchronization primitives for the shared channel.
    //
    if (SUCCEEDED(hr))
    {
        hr = m_controlChannelPolicy.m_notificationEvent.CreateOrOpen(ControlChannelSemaphoreName);
    }

    if (SUCCEEDED(hr))
    {
        hr = m_feedbackChannelPolicy.m_notificationEvent.CreateOrOpen(FeedbackChannelSemaphoreName);
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContextInitializer::CreateAnonymousSharedMemory
//
// PURPOSE:
//  Creates anonymous shared memory.
//
// NOTES:
//  If the agent is running, the functions sends the file descriptor
//  using Unix domain socket.
//
template<typename TSharedMemoryView>
_Must_inspect_result_
HRESULT AnonymousMemoryMlosContextInitializer::CreateAnonymousSharedMemory(
    _In_ FileDescriptorExchange& fileDescriptorExchange,
    _Inout_ TSharedMemoryView& sharedMemory,
    _In_ Internal::MemoryRegionId memoryRegionId,
    _In_ std::size_t sharedMemorySize)
{
    int anonymousSharedMapFd;
    size_t anonymousSharedMapSize;

    HRESULT hr = S_OK;

    if (fileDescriptorExchange.IsServerAvailable())
    {
        // Check if the agent has a given memory region.
        //
        hr = fileDescriptorExchange.GetFileDescriptor(
                memoryRegionId,
                anonymousSharedMapFd,
                anonymousSharedMapSize);
    }

    if (SUCCEEDED(hr) && fileDescriptorExchange.IsServerAvailable())
    {
        // The agent has the memory region, open a shared memory from the received file descriptor.
        //
        hr = sharedMemory.OpenExistingFromFileDescriptor(anonymousSharedMapFd, anonymousSharedMapSize);
    }
    else
    {
        // Create a new anonymous shared memory.
        //
        hr = sharedMemory.CreateAnonymous(sharedMemorySize);
        if (SUCCEEDED(hr))
        {
            // If connected try to send a file descriptor to the agent.
            //
            if (fileDescriptorExchange.IsServerAvailable())
            {
                hr = fileDescriptorExchange.SendFileDescriptor(
                        memoryRegionId,
                        sharedMemory.GetFileDescriptor(),
                        sharedMemorySize);
            }
        }
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContext::Constructor
//
// PURPOSE:
//  Creates InterProcessMlosContext.
//
// NOTES:
//
AnonymousMemoryMlosContext::AnonymousMemoryMlosContext(_In_ AnonymousMemoryMlosContextInitializer&& initializer) noexcept
  : MlosContext(initializer.m_globalMemoryRegionView.MemoryRegion(), m_controlChannel, m_controlChannel, m_feedbackChannel),
    m_contextInitializer(std::move(initializer)),
    m_controlChannel(
        m_contextInitializer.m_globalMemoryRegionView.MemoryRegion().ControlChannelSynchronization,
        m_contextInitializer.m_controlChannelMemoryMapView,
        std::move(m_contextInitializer.m_controlChannelPolicy)),
    m_feedbackChannel(
        m_contextInitializer.m_globalMemoryRegionView.MemoryRegion().FeedbackChannelSynchronization,
        m_contextInitializer.m_feedbackChannelMemoryMapView,
        std::move(m_contextInitializer.m_feedbackChannelPolicy))
{
    m_sharedConfigManager.AssignSharedConfigMemoryRegion(std::move(m_contextInitializer.m_sharedConfigMemoryRegionView));
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContext::Destructor
//
// PURPOSE:
//  Destroys AnonymousMemoryMlosContext object.
//
// NOTES:
//
AnonymousMemoryMlosContext::~AnonymousMemoryMlosContext()
{
    // Decrease the usage counter. Ignore the result.
    // Shared memory is anonymous and it is destroyed once the agent and the target process terminates.
    //
    uint32_t usageCount = m_globalMemoryRegion.AttachedProcessesCount.fetch_sub(1);
    if (usageCount == 1)
    {
        // This is the last process using shared memory map.
        //
        m_controlChannel.ChannelPolicy.m_notificationEvent.CleanupOnClose = true;
        m_feedbackChannel.ChannelPolicy.m_notificationEvent.CleanupOnClose = true;

        // Close all the shared config memory regions.
        //
        m_sharedConfigManager.CleanupOnClose = true;
    }
}

//----------------------------------------------------------------------------
// NAME: MlosContextFactory<AnonymousMemoryMlosContext>::Create
//
// PURPOSE:
//  Creates an AnonymousMemoryMlosContext instance.
//
template<>
_Must_inspect_result_
HRESULT MlosContextFactory<AnonymousMemoryMlosContext>::Create()
{
    typename AnonymousMemoryMlosContext::InitializerType initializer;
    HRESULT hr = initializer.Initialize();
    if (SUCCEEDED(hr))
    {
        // Move context.
        //
        m_context.Initialize(std::move(initializer));

        AnonymousMemoryMlosContext& mlosContext = m_context;

        // #TODO use MlosPlatform
        //
        std::thread fdExchange(
            [&mlosContext]
        {
            HRESULT hr = static_cast<AnonymousMemoryMlosContext&>(mlosContext).HandleFdRequests();
            MLOS_UNUSED_ARG(hr);
        });
        fdExchange.detach();
    }

    return hr;
}
}
}
