//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedChannelPolicies.h
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
// NAME: InternalSharedChannelPolicy
//
// PURPOSE:
//  Internal shared channel policy.
//
// NOTES:
//  Should be used within a single process only.
//  The policy does not provide OS notification. Therefore it is not able to signal the external process.
//
struct InternalSharedChannelPolicy
{
    // Called when received a frame with mismatch codegen type metadata.
    //
    inline void ReceivedInvalidFrame()
    {
        throw std::exception();
    }

    /// <summary>
    /// Notify reader that there is a frame to process.
    /// </summary>
    inline void NotifyExternalReader()
    {}

    // Called when reader thread is no longer processing the messages.
    //
    inline void WaitForFrame()
    {}
};

//----------------------------------------------------------------------------
// NAME: InterProcessSharedChannelPolicy
//
// PURPOSE:
//  Shared channel policy to communicate with Mlos.Agent.
//
// NOTES:
//
struct InterProcessSharedChannelPolicy
{
    InterProcessSharedChannelPolicy() noexcept
    {}

    InterProcessSharedChannelPolicy(InterProcessSharedChannelPolicy&& channelPolicy) noexcept
      : m_notificationEvent(std::move(channelPolicy.m_notificationEvent))
    {
    }

    // Received a frame with mismatch codegen type metadata.
    //
    inline void ReceivedInvalidFrame()
    {}

    inline void NotifyExternalReader()
    {
        m_notificationEvent.Signal();
    }

    // Called when reader thread is no longer processing the messages.
    // We will wait until the writer thread (residing in the external process) signals there is a new message available.
    //
    inline void WaitForFrame()
    {
        m_notificationEvent.Wait();
    }

public:
    // External notification.
    //
    NamedEvent m_notificationEvent;
};

//----------------------------------------------------------------------------
// NAME: SharedChannelSpinPolicy
//
// PURPOSE:
//  Default shared channel policy.
//
// NOTES:
//
struct SharedChannelSpinPolicy
{
public:
    // Called when there is no frame in the buffer.
    //
    inline void WaitForNewFrame()
    {}

    // Called when reader acquire the frame but the frame is not yet completed.
    //
    inline void WaitForFrameCompletion()
    {}

    // There is a frame in the buffer however other thread acquire the read first.
    //
    inline void FailedToAcquireReadRegion()
    {}

    // Another writer acquired the write region.
    //
    inline void FailedToAcquireWriteRegion()
    {}
};

//----------------------------------------------------------------------------
// NAME: TestSharedChannel
//
// PURPOSE:
//  Test shared channel. Shared channel with default policies.
//
// NOTES:
//  Suitable for testing purposes only.
//
using TestSharedChannel = Mlos::Core::SharedChannel<InternalSharedChannelPolicy, SharedChannelSpinPolicy>;

//----------------------------------------------------------------------------
// NAME: InterProcessSharedChannel
//
// PURPOSE:
//  Inter-process shared channel.
//
// NOTES:
//  Shared channel to communicate with Mlos.Agent.
//
using InterProcessSharedChannel = Mlos::Core::SharedChannel<InterProcessSharedChannelPolicy, SharedChannelSpinPolicy>;
}
}
