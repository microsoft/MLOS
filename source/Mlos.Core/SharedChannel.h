//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedChannel.h
//
// Purpose:
//      <description>
//
// Notes:
//      <special-instructions>
//
//*********************************************************************

#pragma once

#include "BytePtr.h"

namespace Mlos
{
namespace Core
{
// Notifies the reader threads that the frame is available to process.
//
void SignalFrameIsReady(
    _Inout_ FrameHeader& frame,
    _In_ int32_t frameLength);

// Notifies the cleanup thread, that the frame has been processed.
//
void SignalFrameForCleanup(
    _Inout_ FrameHeader& frame,
    _In_ int32_t frameLength);

//----------------------------------------------------------------------------
// NAME: ISharedChannel
//
// PURPOSE:
//  Defines SharedChannel interface.
//  SharedChannel<TChannelPolicy, TChannelSpinPolicy> inherits from this class and implements send and receive functionality with given TChannelSpinPolicy and TChannelWaitPolicy.
//  TChannelPolicy is responsible for how channel waits for the notification from the external process (Mlos.Agent).
//  TChannelSpinPolicy control how channel implements spinning when waiting for the frames.
//
// NOTES:
//
class ISharedChannel
{
public:
    ISharedChannel(Mlos::Core::ChannelSynchronization& sync, Mlos::Core::BytePtr buffer, uint32_t size)
      : Sync(sync),
        Buffer(buffer),
        Size(1 << most_significant_bit(size)),
        Margin(Size - sizeof(FrameHeader))
    {
        // Buffer size requirements:
        // - Buffer size must be aligned to sizeof(uint32_t).
        // - To handle position (uint32_t) overflow,
        //    Size of the buffer must satisfy the following condition:
        //    uint32_t.max +1 % Buffer.Size == 0.
        //

        // Check if user passed optimal buffer size value.
        //
        assert(size == Size);

        // Initialize channel.
        //
        InitializeChannel();
    }

    virtual uint32_t AcquireWriteRegionForFrame(int32_t& frameLength) = 0;

    virtual void ProcessMessages(DispatchEntry* dispatchTable, size_t dispatchEntryCount) = 0;

    virtual void NotifyExternalReader() = 0;

    // Returns true if there are reader threads waiting for external process.
    //
    inline bool HasReadersInWaitingState() const;

    // Send the message object.
    //
    template<typename TMessage>
    inline void SendMessage(const TMessage& object);

    // Follows free links until we reach read position.
    //
    void AdvanceFreePosition();

    // Initializes the channel.
    //
    void InitializeChannel();

protected:
    inline FrameHeader& Frame(uint32_t offset);

    inline BytePtr Payload(uint32_t writeOffset);

    inline void ClearPayload(
        _In_ uint32_t writeOffset,
        _In_ uint32_t frameLength)
    {
        memset(Buffer.Pointer + writeOffset + sizeof(uint32_t), 0, frameLength - sizeof(uint32_t));
    }

    inline void ClearLinkPayload(
        _In_ uint32_t writeOffset,
        _In_ uint32_t frameLength,
        _In_ uint32_t bufferSize)
    {
        writeOffset += sizeof(uint32_t);
        frameLength -= sizeof(uint32_t);

        if (writeOffset + frameLength > bufferSize)
        {
            // Overlapped link.
            //
            memset(Buffer.Pointer + writeOffset, 0, bufferSize - writeOffset);
            memset(Buffer.Pointer, 0, frameLength + (writeOffset - bufferSize));
        }
        else
        {
            memset(Buffer.Pointer + writeOffset, 0, frameLength);
        }
    }

public:
    ChannelSynchronization& Sync;

    BytePtr Buffer;

    // Size of the buffer.
    //
    uint32_t Size;

    // Size of the buffer - sizeof(FrameHeader);
    //
    uint32_t Margin;
};

//----------------------------------------------------------------------------
// NAME: SharedChannel<TChannelPolicy, TChannelSpinPolicy>
//
// PURPOSE:
//  Shared channel implementation.
//
// NOTES:
//
template<typename TChannelPolicy, typename TChannelSpinPolicy>
class SharedChannel : public ISharedChannel
{
public:
    SharedChannel(
        _In_ Mlos::Core::ChannelSynchronization& sync,
        _In_ Mlos::Core::BytePtr buffer,
        _In_ uint32_t size,
        _In_ TChannelPolicy channelPolicy = TChannelPolicy()) noexcept
      : ISharedChannel(sync, buffer, size),
        ChannelPolicy(std::move(channelPolicy))
    {
    }

    SharedChannel(
        _In_ Mlos::Core::ChannelSynchronization& sync,
        _In_ Mlos::Core::SharedMemoryMapView& channelMemoryMapView,
        _In_ TChannelPolicy channelPolicy = TChannelPolicy()) noexcept
      : SharedChannel(
            sync,
            channelMemoryMapView.Buffer,
            static_cast<uint32_t>(channelMemoryMapView.MemSize),
            std::move(channelPolicy))
    {
    }

public:
    void ProcessMessages(
        _In_reads_(dispatchEntryCount) DispatchEntry * dispatchTable,
        _In_ size_t dispatchEntryCount) override;

    bool WaitAndDispatchFrame(
        _In_reads_(dispatchEntryCount) DispatchEntry * dispatchTable,
        _In_ size_t dispatchEntryCount);

public:
    TChannelPolicy ChannelPolicy;

private:
    virtual uint32_t AcquireWriteRegionForFrame(_Inout_ int32_t& frameLength) override;

    virtual void NotifyExternalReader() override;

    uint32_t AcquireRegionForWrite(_Inout_ int32_t& frameLength);

    uint32_t WaitForFrame();
};
}
}
