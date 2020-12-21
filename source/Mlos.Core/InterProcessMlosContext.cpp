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
const char* const ControlChannelMemoryMapName = "Host_Mlos.ControlChannel";
const char* const FeedbackChannelMemoryMapName = "Host_Mlos.FeedbackChannel";

// Synchronization OS primitive names.
//
const char* const ControlChannelEventName = "Global\\ControlChannel_Event";
const char* const FeedbackChannelEventName = "Global\\FeedbackChannel_Event";
const char* const TargetProcessEventName = "Global\\Mlos_Global";
// Shared memory mapping name for to store shared configs.
//
const char* const ApplicationConfigSharedMemoryName = "Host_Mlos.Config.SharedMemory";

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
    return InterProcessMlosContext::Create(mlosContextInstance, Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
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
    _In_ size_t sharedConfigMemorySize)
{
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

    // Notification event signaled after the target process initialized Mlos context.
    //
    NamedEvent targetProcessNamedEvent;

    HRESULT hr = globalMemoryRegionView.CreateOrOpen(GlobalMemoryMapName, Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    if (SUCCEEDED(hr))
    {
        // Increase the usage counter. When closing global shared memory, we will decrease the counter.
        // If there is no process using the shared memory, we will clean the OS resources. On Windows OS,
        // this is no-op; on Linux, we unlink created files.
        //
        Internal::GlobalMemoryRegion& globalMemoryRegion = globalMemoryRegionView.MemoryRegion();
        globalMemoryRegion.AttachedProcessesCount.fetch_add(1);
    }

    // Control channel.
    //
    if (SUCCEEDED(hr))
    {
        hr = controlChannelMemoryMapView.CreateOrOpen(
            ControlChannelMemoryMapName,
            Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = controlChannelPolicy.m_notificationEvent.CreateOrOpen(ControlChannelEventName);
    }

    // Feedback channel.
    //
    if (SUCCEEDED(hr))
    {
        hr = feedbackChannelMemoryMapView.CreateOrOpen(
            FeedbackChannelMemoryMapName,
            Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = feedbackChannelPolicy.m_notificationEvent.CreateOrOpen(FeedbackChannelEventName);
    }

    // Shared config memory.
    //
    if (SUCCEEDED(hr))
    {
        hr = sharedConfigMemoryRegionView.CreateOrOpen(
            ApplicationConfigSharedMemoryName,
            sharedConfigMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = targetProcessNamedEvent.CreateOrOpen(TargetProcessEventName);
    }

    // Cleanup if we failed to create all resources.
    //
    if (FAILED(hr))
    {
        bool cleanupOnClose = false;
        if (!globalMemoryRegionView.Buffer.IsInvalid())
        {
            // Decrease the usage counter.
            //
            Internal::GlobalMemoryRegion& globalMemoryRegion = globalMemoryRegionView.MemoryRegion();
            const uint32_t usageCount = globalMemoryRegion.AttachedProcessesCount.fetch_sub(1);
            if (usageCount == 1)
            {
                // This is the last process using shared memory map.
                //
                cleanupOnClose = true;
            }
        }

        // Close all the shared maps if we fail to create one.
        //
        globalMemoryRegionView.CleanupOnClose |= cleanupOnClose;
        globalMemoryRegionView.Close();

        controlChannelMemoryMapView.CleanupOnClose |= cleanupOnClose;
        controlChannelMemoryMapView.Close();

        feedbackChannelMemoryMapView.CleanupOnClose |= cleanupOnClose;
        feedbackChannelMemoryMapView.Close();

        controlChannelPolicy.m_notificationEvent.CleanupOnClose |= cleanupOnClose;
        controlChannelPolicy.m_notificationEvent.Close();

        feedbackChannelPolicy.m_notificationEvent.CleanupOnClose |= cleanupOnClose;
        feedbackChannelPolicy.m_notificationEvent.Close();
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
        std::move(targetProcessNamedEvent));

    InterProcessMlosContext& mlosContext = mlosContextInstance;

    // Post-create registrations.
    //
    if (SUCCEEDED(hr))
    {
        // Control channel.
        //
        hr = mlosContext.RegisterSharedMemory(
            Internal::MemoryRegionId{ Internal::MemoryRegionType::ControlChannel, 0 },
            ControlChannelMemoryMapName,
            Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = mlosContext.RegisterNamedEvent(
            Internal::MemoryRegionId{ Internal::MemoryRegionType::ControlChannel, 0 },
            ControlChannelEventName);
    }

    // Feedback channel.
    //
    if (SUCCEEDED(hr))
    {
        hr = mlosContext.RegisterSharedMemory(
            Internal::MemoryRegionId{ Internal::MemoryRegionType::FeedbackChannel, 0 },
            FeedbackChannelMemoryMapName,
            Internal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = mlosContext.RegisterNamedEvent(
            Internal::MemoryRegionId{ Internal::MemoryRegionType::FeedbackChannel, 0 },
            FeedbackChannelEventName);
    }

    // SharedConfig mapping.
    //
    if (SUCCEEDED(hr))
    {
        Internal::SharedConfigMemoryRegion& sharedConfigMemoryRegion = mlosContext.SharedConfigMemoryRegionView().MemoryRegion();

        hr = mlosContext.RegisterSharedMemory(
            sharedConfigMemoryRegion.MemoryHeader.MemoryRegionId,
            ApplicationConfigSharedMemoryName,
            sharedConfigMemoryRegion.MemoryHeader.MemoryRegionSize);
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
    _In_ SharedMemoryRegionView<Internal::SharedConfigMemoryRegion>&& sharedConfigMemoryRegionView,
    _In_ InterProcessSharedChannelPolicy&& controlChannelPolicy,
    _In_ InterProcessSharedChannelPolicy&& feedbackChannelPolicy,
    _In_ NamedEvent targetProcessNamedEvent) noexcept
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
    m_sharedConfigManager.AssignSharedConfigMemoryRegion(std::move(sharedConfigMemoryRegionView));
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
    const uint32_t usageCount = m_globalMemoryRegion.AttachedProcessesCount.fetch_sub(1);
    if (usageCount == 1)
    {
        // This is the last process using shared memory map.
        //
        m_globalMemoryRegionView.CleanupOnClose = true;
        m_controlChannelMemoryMapView.CleanupOnClose = true;
        m_feedbackChannelMemoryMapView.CleanupOnClose = true;
        m_controlChannel.ChannelPolicy.m_notificationEvent.CleanupOnClose = true;
        m_feedbackChannel.ChannelPolicy.m_notificationEvent.CleanupOnClose = true;
        m_targetProcessNamedEvent.CleanupOnClose = true;

        // Close all the shared config memory regions.
        //
        m_sharedConfigManager.CleanupOnClose = true;
    }
}
}
}
