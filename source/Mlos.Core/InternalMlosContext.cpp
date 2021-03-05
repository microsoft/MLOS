//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: InternalMlosContext.cpp
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
const char* const TestGlobalMemoryMapName = "Test_Mlos.GlobalMemory";

//----------------------------------------------------------------------------
// NAME: InternalMlosContextInitializer::Create
//
// PURPOSE:
//  Creates the shared memory used for the communication channel.
//
// NOTES:
//
_Must_inspect_result_
HRESULT InternalMlosContext::Create(_Inout_ AlignedInstance<InternalMlosContext>& mlosContextInstance)
{
    HRESULT hr = S_OK;

    // Global shared memory region.
    //
    SharedMemoryMapView globalMemoryMapView;

    // Named shared memory for Telemetry and Control Channel.
    //
    SharedMemoryMapView controlChannelMemoryMapView;
    SharedMemoryMapView feedbackChannelMemoryMapView;

    if (SUCCEEDED(hr))
    {
        hr = globalMemoryMapView.CreateNew(TestGlobalMemoryMapName, MlosInternal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    SharedMemoryRegionView<Internal::GlobalMemoryRegion> globalMemoryRegionView(std::move(globalMemoryMapView));

    if (SUCCEEDED(hr))
    {
        hr = controlChannelMemoryMapView.CreateNew(
            "Test_SharedChannelMemory",
            MlosInternal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    if (SUCCEEDED(hr))
    {
        hr = feedbackChannelMemoryMapView.CreateNew(
            "Test_FeedbackChannelMemory",
            MlosInternal::GlobalMemoryRegion::GlobalSharedMemorySize);
    }

    // Create MlosContext.
    //
    mlosContextInstance.Initialize(
        std::move(globalMemoryRegionView),
        std::move(controlChannelMemoryMapView),
        std::move(feedbackChannelMemoryMapView));

    InternalMlosContext& mlosContext = mlosContextInstance;

    // Cleanup all the shared maps on close.
    //
    mlosContext.CleanupOnClose = true;

    return hr;
}

//----------------------------------------------------------------------------
// NAME: InternalMlosContext::Constructor
//
// PURPOSE:
//  Creates InternalMlosContext instance.
//
// NOTES:
//
InternalMlosContext::InternalMlosContext(
    _In_ SharedMemoryRegionView<Internal::GlobalMemoryRegion>&& globalMemoryRegionView,
    _In_ SharedMemoryMapView&& controlChannelMemoryMapView,
    _In_ SharedMemoryMapView&& feedbackChannelMemoryMapView) noexcept
  :  MlosContext(globalMemoryRegionView.MemoryRegion(), m_controlChannel, m_controlChannel, m_feedbackChannel),
    m_globalMemoryRegionView(std::move(globalMemoryRegionView)),
    m_controlChannelMemoryMapView(std::move(controlChannelMemoryMapView)),
    m_feedbackChannelMemoryMapView(std::move(feedbackChannelMemoryMapView)),
    m_controlChannel(
        m_globalMemoryRegionView.MemoryRegion().ControlChannelSynchronization,
        m_controlChannelMemoryMapView),
    m_feedbackChannel(
        m_globalMemoryRegionView.MemoryRegion().FeedbackChannelSynchronization,
        m_feedbackChannelMemoryMapView)
{
}

//----------------------------------------------------------------------------
// NAME: InternalMlosContext::Destructor
//
// PURPOSE:
//  Destroys InternalMlosContext object.
//
// NOTES:
//
InternalMlosContext::~InternalMlosContext()
{
    m_sharedConfigManager.CleanupOnClose |= CleanupOnClose;
    m_globalMemoryRegionView.Close(CleanupOnClose);
    m_controlChannelMemoryMapView.Close(CleanupOnClose);
    m_feedbackChannelMemoryMapView.Close(CleanupOnClose);
}
}
}
