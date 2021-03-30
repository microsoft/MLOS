//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: InterProcessMlosContext.cpp
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

namespace Mlos
{
namespace Core
{
// Shared memory mapping name must start with "Host_" prefix, to be accessible from certain applications.
//
const char* const GlobalMemoryMapName = "Host_Mlos.GlobalMemory";

// Synchronization OS primitive names.
//
const char* const TargetProcessEventName = "Global\\Mlos_Global";

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContext::Create
//
// PURPOSE:
//  Opens the shared memory and synchronization primitives used for the communication channel.
//
// NOTES:
//
_Must_inspect_result_
HRESULT InterProcessMlosContext::Create(_Inout_ AlignedInstance<InterProcessMlosContext>& mlosContextInstance)
{
    return InterProcessMlosContext::Create(mlosContextInstance, MlosInternal::GlobalMemoryRegion::GlobalSharedMemorySize);
}

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContext::Create
//
// PURPOSE:
//  Opens the shared memory and synchronization primitives used for the communication channel.
//
// NOTES:
//
_Must_inspect_result_
HRESULT InterProcessMlosContext::Create(
    _Inout_ AlignedInstance<InterProcessMlosContext>& mlosContextInstance,
    _In_ size_t configMemorySize)
{
    // Shared channel shared memory and notification primitive.
    //
    SharedMemoryMapView globalMemoryMapView;
    SharedMemoryMapView controlChannelMemoryMapView;
    SharedMemoryMapView feedbackChannelMemoryMapView;
    SharedMemoryMapView sharedConfigMemoryMapView;

    InterProcessSharedChannelPolicy controlChannelPolicy;
    InterProcessSharedChannelPolicy feedbackChannelPolicy;

    // Notification event signaled after the target process initialized Mlos context.
    //
    NamedEvent targetProcessNamedEvent;

    HRESULT hr = globalMemoryMapView.CreateOrOpen(GlobalMemoryMapName, Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    if (FAILED(hr))
    {
        return hr;
    }

    // Global shared memory region.
    //
    SharedMemoryRegionView<Internal::GlobalMemoryRegion> globalMemoryRegionView(std::move(globalMemoryMapView));

    // Increase the usage counter. When closing global shared memory, we will decrease the counter.
    // If there is no process using the shared memory, we will clean the OS resources. On Windows OS,
    // this is no-op; on Linux, we unlink created files.
    //
    Internal::GlobalMemoryRegion& globalMemoryRegion = globalMemoryRegionView.MemoryRegion();
    globalMemoryRegion.AttachedProcessesCount.fetch_add(1);

    if (SUCCEEDED(hr))
    {
        hr = MlosContext::CreateOrOpenSharedMemory(
            globalMemoryRegionView.MemoryRegion(),
            MlosInternal::MemoryRegionId{ MlosInternal::MemoryRegionType::ControlChannel, 0 },
            controlChannelMemoryMapView,
            MlosInternal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = MlosContext::CreateOrOpenSharedMemory(
            globalMemoryRegionView.MemoryRegion(),
            MlosInternal::MemoryRegionId{ MlosInternal::MemoryRegionType::FeedbackChannel, 0 },
            feedbackChannelMemoryMapView,
            MlosInternal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

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
        hr = targetProcessNamedEvent.CreateOrOpen(TargetProcessEventName);
    }

    // Create MlosContext.
    //
    mlosContextInstance.Initialize(
        std::move(globalMemoryRegionView),
        std::move(controlChannelMemoryMapView),
        std::move(feedbackChannelMemoryMapView),
        std::move(controlChannelPolicy),
        std::move(feedbackChannelPolicy),
        std::move(targetProcessNamedEvent));

    InterProcessMlosContext& mlosContext = mlosContextInstance;

    // Cleanup if we failed to create all resources.
    //
    if (FAILED(hr))
    {
        if (!mlosContext.m_globalMemoryRegionView.IsInvalid())
        {
            // Decrease the usage counter.
            //
            const uint32_t usageCount = globalMemoryRegion.AttachedProcessesCount.fetch_sub(1);
            if (usageCount == 1)
            {
                // This is the last process using shared memory map.
                //
                mlosContext.CleanupOnClose = true;
            }
        }
    }

    // Shared config memory.
    //
    if (SUCCEEDED(hr))
    {
        hr = MlosContext::CreateOrOpenSharedMemory(
            mlosContext.m_globalMemoryRegion,
            MlosInternal::MemoryRegionId { MlosInternal::MemoryRegionType::SharedConfig, 0 },
            sharedConfigMemoryMapView,
            configMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        MlosCore::SharedMemoryRegionView<MlosInternal::SharedConfigMemoryRegion> sharedConfigMemoryRegionView(std::move(
            sharedConfigMemoryMapView));

        mlosContext.m_sharedConfigManager.AssignSharedConfigMemoryRegion(std::move(sharedConfigMemoryRegionView));
    }

    // The context is created, signal the notification event,
    //
    if (SUCCEEDED(hr))
    {
        hr = mlosContext.m_targetProcessNamedEvent.Signal();
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
InterProcessMlosContext::InterProcessMlosContext(
    _In_ SharedMemoryRegionView<Internal::GlobalMemoryRegion>&& globalMemoryRegionView,
    _In_ SharedMemoryMapView&& controlChannelMemoryMapView,
    _In_ SharedMemoryMapView&& feedbackChannelMemoryMapView,
    _In_ InterProcessSharedChannelPolicy&& controlChannelPolicy,
    _In_ InterProcessSharedChannelPolicy&& feedbackChannelPolicy,
    _In_ NamedEvent&& targetProcessNamedEvent) noexcept
  : MlosContext(globalMemoryRegionView.MemoryRegion(), m_controlChannel, m_controlChannel, m_feedbackChannel),
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
    m_targetProcessNamedEvent(std::move(targetProcessNamedEvent))
{
}

//----------------------------------------------------------------------------
// NAME: InterProcessMlosContext::Destructor
//
// PURPOSE:
//  Destroys InterProcessMlosContext object.
//
// NOTES:
//
InterProcessMlosContext::~InterProcessMlosContext()
{
    // Decrease the usage counter.
    //
    if (!m_globalMemoryRegionView.IsInvalid())
    {
        const uint32_t usageCount = m_globalMemoryRegion.AttachedProcessesCount.fetch_sub(1);
        CleanupOnClose |= usageCount == 1;
    }

    m_sharedConfigManager.CleanupOnClose |= CleanupOnClose;

    // This is the last process using shared memory map.
    //
    m_globalMemoryRegionView.Close(CleanupOnClose);
    m_controlChannelMemoryMapView.Close(CleanupOnClose);
    m_feedbackChannelMemoryMapView.Close(CleanupOnClose);
    m_controlChannel.ChannelPolicy.m_notificationEvent.Close(CleanupOnClose);
    m_feedbackChannel.ChannelPolicy.m_notificationEvent.Close(CleanupOnClose);
    m_targetProcessNamedEvent.Close(CleanupOnClose);
}
}
}
