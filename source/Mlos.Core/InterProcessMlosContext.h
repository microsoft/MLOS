//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: InterProcessMlosContext.h
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
// NAME: InterProcessMlosContext
//
// PURPOSE:
//  Implementation of an inter-process MlosContext.
//
// NOTES:
//
class InterProcessMlosContext : public MlosContext
{
public:
    _Must_inspect_result_
    HRESULT static Create(_Inout_ AlignedInstance<InterProcessMlosContext>& mlosContextInstance);

    _Must_inspect_result_
    HRESULT static Create(
        _Inout_ AlignedInstance<InterProcessMlosContext>& mlosContextInstance,
        _In_ size_t configMemorySize);

    InterProcessMlosContext(
        _In_ SharedMemoryRegionView<Internal::GlobalMemoryRegion>&& globalMemoryRegionView,
        _In_ SharedMemoryMapView&& controlChannelMemoryMapView,
        _In_ SharedMemoryMapView&& feedbackChannelMemoryMapView,
        _In_ InterProcessSharedChannelPolicy&& controlChannelPolicy,
        _In_ InterProcessSharedChannelPolicy&& feedbackChannelPolicy,
        _In_ NamedEvent&& targetProcessNamedEvent) noexcept;

    InterProcessMlosContext(_In_ const InterProcessMlosContext&) = delete;

    InterProcessMlosContext& operator=(_In_ const InterProcessMlosContext&) = delete;

    ~InterProcessMlosContext();

private:
    // Global shared memory region.
    //
    SharedMemoryRegionView<Internal::GlobalMemoryRegion> m_globalMemoryRegionView;

    // Named shared memory for Telemetry and Control Channel.
    //
    SharedMemoryMapView m_controlChannelMemoryMapView;

    // Named shared memory for Feedback Channel.
    //
    SharedMemoryMapView m_feedbackChannelMemoryMapView;

    // Named shared memory for Telemetry and Control Channel.
    //
    InterProcessSharedChannel m_controlChannel;

    // Named shared memory for Feedback Channel.
    //
    InterProcessSharedChannel m_feedbackChannel;

    // Notification event signaled after the target process initialized Mlos context.
    //
    NamedEvent m_targetProcessNamedEvent;

    friend class MlosInitializer<InterProcessMlosContext>;
};
}
}
