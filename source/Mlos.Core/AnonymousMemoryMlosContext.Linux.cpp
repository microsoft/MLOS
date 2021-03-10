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
#include "Mlos.Core.inl"

#include <cstdio>

namespace Mlos
{
namespace Core
{
// File exchange Unix domain socket name.
//
const char* const MlosSocketFileName = "mlos.sock";
const char* const MlosOpenedFileName = "mlos.opened";

const char* const GlobalMemoryMapName = "Host_Mlos.GlobalMemory";

const char* const DefaultSocketFolderPath = "/var/tmp/mlos/";

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
_Must_inspect_result_
HRESULT CreateOrOpenAnonymousSharedMemory(
    _In_ FileDescriptorExchange& fileDescriptorExchange,
    _Inout_ SharedMemoryMapView& sharedMemoryMapView,
    _In_z_ const char* sharedMemoryMapName,
    _In_ std::size_t sharedMemorySize)
{
    int32_t anonymousSharedMapFd;

    HRESULT hr = S_OK;

    if (fileDescriptorExchange.IsServerAvailable())
    {
        // Check if the agent has a given memory region.
        //
        hr = fileDescriptorExchange.GetFileDescriptor(
            sharedMemoryMapName,
            anonymousSharedMapFd);
    }

    if (SUCCEEDED(hr) && fileDescriptorExchange.IsServerAvailable())
    {
        // The agent has the memory region, open a shared memory from the received file descriptor.
        //
        hr = sharedMemoryMapView.OpenExistingFromFileDescriptor(
            sharedMemoryMapName,
            anonymousSharedMapFd);
    }
    else
    {
        // Create a new anonymous shared memory.
        //
        hr = sharedMemoryMapView.CreateAnonymous(
                sharedMemoryMapName,
                sharedMemorySize);
        if (SUCCEEDED(hr))
        {
            // If connected try to send a file descriptor to the agent.
            //
            if (fileDescriptorExchange.IsServerAvailable())
            {
                hr = fileDescriptorExchange.SendFileDescriptor(
                    sharedMemoryMapName,
                    sharedMemoryMapView.GetFileDescriptor());
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

    char* socketFilePath = nullptr;
    if (asprintf(&socketFilePath, "%s/%s", socketFolderPath, MlosSocketFileName) == -1)
    {
        hr = E_OUTOFMEMORY;
    }

    // Try to connect to the Mlos.Agent Unix domain socket.
    // If the agent is unavailable and we fail to connect,
    // we will send the file mappings after the agent becomes available
    // (AnonymousMemoryMlosContext::HandleFdRequests).
    //
    FileDescriptorExchange fileDescriptorExchange;
    if (SUCCEEDED(hr))
    {
        HRESULT hrIgnored = fileDescriptorExchange.Connect(socketFilePath);
        MLOS_UNUSED_ARG(hrIgnored);
    }

    // Shared channel shared memory and notification primitive.
    //
    SharedMemoryMapView globalMemoryMapView;
    SharedMemoryMapView controlChannelMemoryMapView;
    SharedMemoryMapView feedbackChannelMemoryMapView;
    SharedMemoryMapView sharedConfigMemoryMapView;

    InterProcessSharedChannelPolicy controlChannelPolicy;
    InterProcessSharedChannelPolicy feedbackChannelPolicy;

    FileWatchEvent fileWatchEvent;

    // Global shared memory region.
    //
    if (SUCCEEDED(hr))
    {
        // Create global shared memory.
        //
        hr = CreateOrOpenAnonymousSharedMemory(
            fileDescriptorExchange,
            globalMemoryMapView,
            GlobalMemoryMapName,
            Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    // Global shared memory region.
    //
    SharedMemoryRegionView<Internal::GlobalMemoryRegion> globalMemoryRegionView(std::move(globalMemoryMapView));

    if (SUCCEEDED(hr))
    {
        // Increase the usage counter.
        //
        Internal::GlobalMemoryRegion& globalMemoryRegion = globalMemoryRegionView.MemoryRegion();
        globalMemoryRegion.AttachedProcessesCount.fetch_add(1);
    }

    // Create control channel shared memory.
    //
    if (SUCCEEDED(hr))
    {
        hr = AnonymousMemoryMlosContext::CreateOrOpenSharedMemory(
                fileDescriptorExchange,
                globalMemoryRegionView.MemoryRegion(),
                Internal::MemoryRegionId { Internal::MemoryRegionType::ControlChannel, 0 },
                controlChannelMemoryMapView,
                Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = AnonymousMemoryMlosContext::CreateOrOpenSharedMemory(
                fileDescriptorExchange,
                globalMemoryRegionView.MemoryRegion(),
                Internal::MemoryRegionId { Internal::MemoryRegionType::FeedbackChannel, 0 },
                feedbackChannelMemoryMapView,
                Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    // Create shared config memory.
    //
    if (SUCCEEDED(hr))
    {
        hr = AnonymousMemoryMlosContext::CreateOrOpenSharedMemory(
                fileDescriptorExchange,
                globalMemoryRegionView.MemoryRegion(),
                Internal::MemoryRegionId { Internal::MemoryRegionType::SharedConfig, 0 },
                sharedConfigMemoryMapView,
                sharedConfigMemorySize);
    }

    // NotificationEvents.
    //
    if (SUCCEEDED(hr))
    {
        hr = MlosContext::CreateOrOpenNamedEvent(
            globalMemoryRegionView.MemoryRegion(),
            MlosInternal::MemoryRegionId{ MlosInternal::MemoryRegionType::ControlChannel, 0 },
            controlChannelPolicy.m_notificationEvent);
    }

    if (SUCCEEDED(hr))
    {
        hr = MlosContext::CreateOrOpenNamedEvent(
            globalMemoryRegionView.MemoryRegion(),
            MlosInternal::MemoryRegionId{ MlosInternal::MemoryRegionType::FeedbackChannel, 0 },
            feedbackChannelPolicy.m_notificationEvent);
    }

    if (SUCCEEDED(hr))
    {
        hr = fileWatchEvent.Initialize(socketFolderPath, MlosOpenedFileName);
    }

    // Create MlosContext.
    //
    mlosContextInstance.Initialize(
        std::move(globalMemoryRegionView),
        std::move(controlChannelMemoryMapView),
        std::move(feedbackChannelMemoryMapView),
        std::move(sharedConfigMemoryMapView),
        std::move(controlChannelPolicy),
        std::move(feedbackChannelPolicy),
        std::move(fileWatchEvent),
        socketFilePath);

    AnonymousMemoryMlosContext& mlosContext = mlosContextInstance;

    // Create a thread that will wait for the agent and will send the file descriptors.
    //
    if (SUCCEEDED(hr))
    {
        hr = Mlos::Core::MlosPlatform::CreateThread(
            AnonymousMemoryMlosContext::HandleFdRequestsThreadProc,
            &mlosContext,
            mlosContext.m_fdExchangeThread);
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContext::CreateOrOpenSharedMemory
//
// PURPOSE:
//  Creates new or opens existing shared memory map.
//
// RETURNS:
//
// NOTES:
//  Configurations for the created shared memory maps are stored in the global memory region dictionary.
//
_Must_inspect_result_
HRESULT AnonymousMemoryMlosContext::CreateOrOpenSharedMemory(
    _In_ FileDescriptorExchange& fileDescriptorExchange,
    _In_ MlosInternal::GlobalMemoryRegion& globalMemoryRegion,
    _In_ MlosInternal::MemoryRegionId memoryRegionId,
    _Inout_ MlosCore::SharedMemoryMapView& sharedMemoryMapView,
    _In_ const size_t memSize)
{
    // Locate existing config.
    //
    MlosCore::ComponentConfig<MlosInternal::RegisteredMemoryRegionConfig> registeredMemoryRegion;
    registeredMemoryRegion.MemoryRegionId = memoryRegionId;

    HRESULT hr = MlosCore::SharedConfigManager::Lookup(
        globalMemoryRegion.SharedConfigDictionary,
        registeredMemoryRegion);

    if (SUCCEEDED(hr))
    {
        const MlosCore::StringPtr memoryMapName = registeredMemoryRegion.Proxy().MemoryMapName();

        hr = CreateOrOpenAnonymousSharedMemory(
            fileDescriptorExchange,
            sharedMemoryMapView,
            memoryMapName.Data,
            memSize);
    }
    else
    {
        const MlosCore::UniqueString memoryMapName;

        hr = CreateOrOpenAnonymousSharedMemory(
            fileDescriptorExchange,
            sharedMemoryMapView,
            memoryMapName.Str(),
            memSize);

        if (SUCCEEDED(hr))
        {
            registeredMemoryRegion.MemoryRegionId = memoryRegionId;
            registeredMemoryRegion.MemoryMapName = memoryMapName.Str();
            registeredMemoryRegion.MemoryRegionSize = memSize;

            hr = MlosCore::SharedConfigManager::CreateOrUpdateFrom(
                globalMemoryRegion.SharedConfigDictionary,
                registeredMemoryRegion);
        }
    }

    return hr;
}

//----------------------------------------------------------------------------
// NAME: AnonymousMemoryMlosContext::HandleFdRequestsThreadProc
//
// PURPOSE:
//
// NOTES:
//
void* AnonymousMemoryMlosContext::HandleFdRequestsThreadProc(_In_ void* pParam)
{
    AnonymousMemoryMlosContext* pAnonymousMemoryMlosContext = reinterpret_cast<AnonymousMemoryMlosContext*>(pParam);
    MLOS_RETAIL_ASSERT(pAnonymousMemoryMlosContext != nullptr);

    HRESULT hr = pAnonymousMemoryMlosContext->HandleFdRequests();
    MLOS_RETAIL_ASSERT(SUCCEEDED(hr));

    return nullptr;
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

    // Request loop.
    //
    while (SUCCEEDED(hr))
    {
        hr = m_fileWatchEvent.Wait();
        if (FAILED(hr))
        {
            if (m_fileWatchEvent.IsInvalid())
            {
                // The notification fd has been closed.
                //
                hr = S_OK;
            }

            // Terminate the process as it us unsafe to continue.
            //
            return hr;
        }

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
                GlobalMemoryMapName,
                m_globalMemoryRegionView.MapView().GetFileDescriptor());
        }

        if SUCCEEDED(hr)
        {
            hr = fileDescriptorExchange.SendFileDescriptor(
                m_controlChannelMemoryMapView.GetSharedMemoryMapName(),
                m_controlChannelMemoryMapView.GetFileDescriptor());
        }

        if SUCCEEDED(hr)
        {
            hr = fileDescriptorExchange.SendFileDescriptor(
                m_feedbackChannelMemoryMapView.GetSharedMemoryMapName(),
                m_feedbackChannelMemoryMapView.GetFileDescriptor());
        }

        if SUCCEEDED(hr)
        {
            hr = fileDescriptorExchange.SendFileDescriptor(
                SharedConfigMemoryMapView().GetSharedMemoryMapName(),
                SharedConfigMemoryMapView().GetFileDescriptor());
        }
    }

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
    _In_ FileWatchEvent&& fileWatchEvent,
    _In_z_ char* socketFilePath) noexcept
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
    m_fileWatchEvent(std::move(fileWatchEvent)),
    m_fdExchangeThread(INVALID_THREAD_HANDLE),
    m_socketFilePath(socketFilePath)
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
    // Abort the file watch event wait, that will stop the file descriptor exchange thread.
    //
    m_fileWatchEvent.Abort();

    // Wait for the file descriptor exchange thread to complete.
    //
    HRESULT hr = MlosCore::MlosPlatform::JoinThread(m_fdExchangeThread);
    MLOS_RETAIL_ASSERT(SUCCEEDED(hr));

    // Close the file watch event.
    //
    m_fileWatchEvent.Close();

    free(m_socketFilePath);

    // Decrease the usage counter. Ignore the result.
    // Shared memory is anonymous and it is destroyed once the agent and the target process terminates.
    //
    uint32_t usageCount = m_globalMemoryRegion.AttachedProcessesCount.fetch_sub(1);
    if (usageCount == 1)
    {
        // This is the last process using shared memory map.
        //
        m_controlChannel.ChannelPolicy.m_notificationEvent.Close(true);
        m_feedbackChannel.ChannelPolicy.m_notificationEvent.Close(true);

        // Close all the shared config memory regions.
        //
        m_sharedConfigManager.CleanupOnClose = true;
    }
}
}
}
