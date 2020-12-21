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
#include <sys/inotify.h>
#include <sys/stat.h>
#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <unistd.h>

namespace Mlos
{
namespace Core
{
// File exchange Unix domain socket name.
//
const char* const MlosSocketFileName = "mlos.sock";
const char* const MlosOpenedFileName = "mlos.opened";

const char* const DefaultSocketFolderPath = "/var/tmp/mlos/";

// #TODO remove it, use condition variables mapped to shared memory.
//
const char* const ControlChannelSemaphoreName = "mlos_control_channel_event";
const char* const FeedbackChannelSemaphoreName = "mlos_feedback_channel_event";

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
// #TODO move to FileDescriptorExchange
//
template<typename TSharedMemoryView>
_Must_inspect_result_
HRESULT CreateAnonymousSharedMemory(
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
// NAME: AnonymousMemoryMlosContextInitializer::Create
//
// PURPOSE:
//  Creates AnonymousMemoryMlosContext using anonymous shared memory region.
//
// NOTES:
//  Create using default arguments.
//
_Must_inspect_result_
HRESULT AnonymousMemoryMlosContext::Create(
    _Inout_ AlignedInstance<AnonymousMemoryMlosContext>& mlosContextInstance)
{
    return AnonymousMemoryMlosContext::Create(
        mlosContextInstance,
        DefaultSocketFolderPath,
        Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContextInitializer::Create
//
// PURPOSE:
//  Creates AnonymousMemoryMlosContext using anonymous shared memory region.
//
// NOTES:
//
_Must_inspect_result_
HRESULT AnonymousMemoryMlosContext::Create(
    _Inout_ AlignedInstance<AnonymousMemoryMlosContext>& mlosContextInstance,
    _In_z_ const char* socketFolderPath,
    _In_ size_t sharedConfigMemorySize)
{
    HRESULT hr = S_OK;

    char* directoryPath = nullptr;
    char* socketFilePath = nullptr;
    char* openedFilePath = nullptr;

    directoryPath = strdup(socketFolderPath);
    if (directoryPath == nullptr)
    {
        hr = E_OUTOFMEMORY;
    }

    if (SUCCEEDED(hr))
    {
        if (asprintf(&socketFilePath, "%s/%s", directoryPath, MlosSocketFileName) == -1)
        {
            hr = E_OUTOFMEMORY;
        }
    }

    if (SUCCEEDED(hr))
    {
        if (asprintf(&openedFilePath, "%s/%s", directoryPath, MlosOpenedFileName) == -1)
        {
            hr = E_OUTOFMEMORY;
        }
    }

    if (FAILED(hr))
    {
        free(directoryPath);
        free(socketFilePath);
        free(openedFilePath);
        return hr;
    }

    // Try to connect to the Mlos.Agent Unix domain socket.
    // If the agent is unavailable and we fail to connect,
    // we will send the file mappings after the agent becomes available
    // (AnonymousMemoryMlosContext::HandleFdRequests).
    //
    FileDescriptorExchange fileDescriptorExchange;
    hr = fileDescriptorExchange.Connect(socketFilePath);
    MLOS_IGNORE_HR(hr);

    // Global shared memory region.
    //
    SharedMemoryRegionView<Internal::GlobalMemoryRegion> globalMemoryRegionView;

    // Shared channel shared memory and notification primitive.
    //
    SharedMemoryMapView controlChannelMemoryMapView;
    SharedMemoryMapView feedbackChannelMemoryMapView;
    SharedMemoryRegionView<Internal::SharedConfigMemoryRegion> sharedConfigMemoryRegionView;
    InterProcessSharedChannelPolicy controlChannelPolicy;
    InterProcessSharedChannelPolicy feedbackChannelPolicy;

    {
        // Create global shared memory.
        //
        hr = CreateAnonymousSharedMemory(
                fileDescriptorExchange,
                globalMemoryRegionView,
                Internal::MemoryRegionId { Internal::MemoryRegionType::Global, 0 },
                Internal::GlobalMemoryRegion::GlobalSharedMemorySize);

        // Increase the usage counter.
        //
        Internal::GlobalMemoryRegion& globalMemoryRegion = globalMemoryRegionView.MemoryRegion();
        globalMemoryRegion.AttachedProcessesCount.fetch_add(1);
    }

    // Create control channel shared memory.
    //
    if (SUCCEEDED(hr))
    {
        hr = CreateAnonymousSharedMemory(
                fileDescriptorExchange,
                controlChannelMemoryMapView,
                Internal::MemoryRegionId { Internal::MemoryRegionType::ControlChannel, 0 },
                Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = CreateAnonymousSharedMemory(
                fileDescriptorExchange,
                feedbackChannelMemoryMapView,
                Internal::MemoryRegionId { Internal::MemoryRegionType::FeedbackChannel, 0 },
                Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    // Create shared config memory.
    //
    if (SUCCEEDED(hr))
    {
        hr = CreateAnonymousSharedMemory(
                fileDescriptorExchange,
                sharedConfigMemoryRegionView,
                Internal::MemoryRegionId { Internal::MemoryRegionType::SharedConfig, 0 },
                sharedConfigMemorySize);
    }

    // Create synchronization primitives for the shared channel.
    //
    if (SUCCEEDED(hr))
    {
        hr = controlChannelPolicy.m_notificationEvent.CreateOrOpen(ControlChannelSemaphoreName);
    }

    if (SUCCEEDED(hr))
    {
        hr = feedbackChannelPolicy.m_notificationEvent.CreateOrOpen(FeedbackChannelSemaphoreName);
    }

    // Create MlosContext.
    //
    mlosContextInstance.Initialize(
        std::move(globalMemoryRegionView),
        std::move(controlChannelMemoryMapView),
        std::move(feedbackChannelMemoryMapView),
        std::move(sharedConfigMemoryRegionView),
        std::move(controlChannelPolicy),
        std::move(feedbackChannelPolicy),
        directoryPath,
        socketFilePath,
        openedFilePath);

    AnonymousMemoryMlosContext& mlosContext = mlosContextInstance;

    // Register semaphores in the global memory.
    //
    if (SUCCEEDED(hr))
    {
        hr = mlosContext.RegisterNamedEvent(
            Internal::MemoryRegionId{ Internal::MemoryRegionType::ControlChannel, 0 },
            ControlChannelSemaphoreName);
    }

    if (SUCCEEDED(hr))
    {
        hr = mlosContext.RegisterNamedEvent(
            Internal::MemoryRegionId{ Internal::MemoryRegionType::FeedbackChannel, 0 },
            FeedbackChannelSemaphoreName);
    }

    // Create a thread that will wait for the agent and will send the file descriptors.
    //
    if (SUCCEEDED(hr))
    {
        hr = Mlos::Core::MlosPlatform::CreateThread(
            AnonymousMemoryMlosContext::HandleFdRequestsThreadProc,
            &mlosContext);
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContext::CreateSocketWatchFile
//
// PURPOSE:
//
// NOTES:
//
_Must_inspect_result_
HRESULT AnonymousMemoryMlosContext::CreateSocketWatchFile()
{
    // Try to create a folder where the file is located, ignore the errors.
    //
    mkdir(m_directoryPath, S_IRWXU | S_IRWXG | S_IRGRP | S_IWGRP);

    // Create the empty file.
    //
    int fdOpenedFile = creat(m_openedFilePath, S_IRWXU | S_IRWXG | S_IRGRP | S_IWGRP);
    if (fdOpenedFile == INVALID_FD_VALUE)
    {
        // Return the failure.
        //
        return HRESULT_FROM_ERRNO(errno);
    }

    // Close the descriptors before opening a watch to avoid close notification.
    //
    close(fdOpenedFile);

    return S_OK;
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContext::HandleFdRequestsThreadProc
//
// PURPOSE:
//
// NOTES:
//
void AnonymousMemoryMlosContext::HandleFdRequestsThreadProc(void* pParam)
{
    AnonymousMemoryMlosContext* pAnonymousMemoryMlosContext = reinterpret_cast<AnonymousMemoryMlosContext*>(pParam);
    MLOS_RETAIL_ASSERT(pAnonymousMemoryMlosContext != nullptr);

    HRESULT hr = pAnonymousMemoryMlosContext->HandleFdRequests();
    MLOS_RETAIL_ASSERT(SUCCEEDED(hr));
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContext::HandleFdRequests
//
// PURPOSE:
//  Function is responsible for sending the shared memory file descriptors.
//  Once the agents starts, it opens a unix domain socket and signals the fd exchange semaphore.
//  Then the function sends all file descriptors from the mlos context.
//
// NOTES:
//  /tmp/mlos/               <- notification folder
//  /tmp/mlos/mlos.socket    <- unix domain socket
//  /tmp/mlos/mlos.opened    <- watch file
//
_Must_inspect_result_
HRESULT AnonymousMemoryMlosContext::HandleFdRequests()
{
    HRESULT hr = S_OK;

    // Create a watch file.
    //
    hr = CreateSocketWatchFile();
    if (FAILED(hr))
    {
        return hr;
    }

    // Create notification.
    //
    int32_t fdNotify = inotify_init();
    int32_t fdWatch = INVALID_FD_VALUE;

    constexpr int NotifyEventSize = sizeof(struct inotify_event);
    constexpr int NotifyEventBufferSize = 2 * (NotifyEventSize + NAME_MAX + 1);

    char eventsBuffer[NotifyEventBufferSize];

    bool waitForSocket = true;

    // Request loop.
    //
    while (SUCCEEDED(hr))
    {
        // Wait for the agent when it is ready to get the file descriptors.
        //
        while (waitForSocket)
        {
            if (fdWatch == INVALID_FD_VALUE)
            {
                // Create the file watch.
                //
                hr = CreateSocketWatchFile();
                if (FAILED(hr))
                {
                    break;
                }

                fdWatch = inotify_add_watch(
                    fdNotify,
                    m_openedFilePath,
                    IN_OPEN | IN_DELETE_SELF);
            }

            if (fdWatch == INVALID_FD_VALUE)
            {
                hr = HRESULT_FROM_ERRNO(errno);
                break;
            }

            int32_t length = read(fdNotify, eventsBuffer, NotifyEventBufferSize);
            if (length < 0)
            {
                // Wait for the notification failed.
                //
                hr = HRESULT_FROM_ERRNO(errno);
                break;
            }

            int32_t i = 0;

            // actually read return the list of change events happens. Here, read the change event one by one and process it accordingly.
            while (waitForSocket && i < length)
            {
                struct inotify_event* pEvent = reinterpret_cast<struct inotify_event *>(&eventsBuffer[i]);

                if (pEvent->mask & IN_OPEN)
                {
                    // The file was opened.
                    //
                    waitForSocket = false;
                    break;
                }
                else if (pEvent->mask & IN_DELETE_SELF)
                {
                    // The file has been deleted, remove the watch and create a new one.
                    //
                    inotify_rm_watch(fdNotify, fdWatch);

                    fdWatch = INVALID_FD_VALUE;
                }

                i += NotifyEventSize + pEvent->len;
            }
        }

        waitForSocket = true;

        // Send the shared memory file descriptors to the agent.
        //
        FileDescriptorExchange fileDescriptorExchange;
        hr = fileDescriptorExchange.Connect(m_socketFilePath);
        if (FAILED(hr))
        {
            // Failed to connect.
            //
            continue;
        }

        if SUCCEEDED(hr)
        {
            hr = fileDescriptorExchange.SendFileDescriptor(
                Internal::MemoryRegionId { Internal::MemoryRegionType::Global, 0 },
                m_globalMemoryRegionView.GetFileDescriptor(),
                m_globalMemoryRegionView.MemSize);
        }

        if SUCCEEDED(hr)
        {
            hr = fileDescriptorExchange.SendFileDescriptor(
                Internal::MemoryRegionId { Internal::MemoryRegionType::ControlChannel, 0 },
                m_controlChannelMemoryMapView.GetFileDescriptor(),
                m_controlChannelMemoryMapView.MemSize);
        }

        if SUCCEEDED(hr)
        {
            hr = fileDescriptorExchange.SendFileDescriptor(
                Internal::MemoryRegionId { Internal::MemoryRegionType::FeedbackChannel, 0 },
                m_feedbackChannelMemoryMapView.GetFileDescriptor(),
                m_feedbackChannelMemoryMapView.MemSize);
        }

        if SUCCEEDED(hr)
        {
            hr = fileDescriptorExchange.SendFileDescriptor(
                Internal::MemoryRegionId { Internal::MemoryRegionType::SharedConfig, 0 },
                SharedConfigMemoryRegionView().GetFileDescriptor(),
                SharedConfigMemoryRegionView().MemSize);
        }
    }

    // Close
    //
    inotify_rm_watch(fdNotify, fdWatch);
    close(fdNotify);

    return hr;
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContext::Constructor
//
// PURPOSE:
//  Creates AnonymousMemoryMlosContext instance.
//
// NOTES:
//
AnonymousMemoryMlosContext::AnonymousMemoryMlosContext(
    _In_ SharedMemoryRegionView<Internal::GlobalMemoryRegion>&& globalMemoryRegionView,
    _In_ SharedMemoryMapView&& controlChannelMemoryMapView,
    _In_ SharedMemoryMapView&& feedbackChannelMemoryMapView,
    _In_ SharedMemoryRegionView<Internal::SharedConfigMemoryRegion>&& sharedConfigMemoryRegionView,
    _In_ InterProcessSharedChannelPolicy&& controlChannelPolicy,
    _In_ InterProcessSharedChannelPolicy&& feedbackChannelPolicy,
    _In_z_ char* directoryPath,
    _In_z_ char* socketFilePath,
    _In_z_ char* openedFilePath) noexcept
 :  MlosContext(globalMemoryRegionView.MemoryRegion(), m_controlChannel, m_controlChannel, m_feedbackChannel),
    m_globalMemoryRegionView(std::move(globalMemoryRegionView)),
    m_controlChannelMemoryMapView(std::move(controlChannelMemoryMapView)),
    m_feedbackChannelMemoryMapView(std::move(feedbackChannelMemoryMapView)),
    m_controlChannel(
        m_globalMemoryRegionView.MemoryRegion().ControlChannelSynchronization,
        m_controlChannelMemoryMapView,
        std::move(controlChannelPolicy)),
    m_feedbackChannel(
        m_globalMemoryRegionView.MemoryRegion().FeedbackChannelSynchronization,
        m_feedbackChannelMemoryMapView,
        std::move(feedbackChannelPolicy)),
    m_directoryPath(directoryPath),
    m_socketFilePath(socketFilePath),
    m_openedFilePath(openedFilePath)
{
    m_sharedConfigManager.AssignSharedConfigMemoryRegion(std::move(sharedConfigMemoryRegionView));
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
    free(m_directoryPath);
    free(m_socketFilePath);
    free(m_openedFilePath);

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
}
}
