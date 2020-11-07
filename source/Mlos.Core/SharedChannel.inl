//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedConfig.inl
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
// NAME: ISharedChannel::HasReadersInWaitingState
//
// RETURNS:
//  Returns true if channel has readers in waiting state.
//
bool ISharedChannel::HasReadersInWaitingState() const
{
    return Sync.ReaderInWaitingStateCount.load(std::memory_order_acquire);
}

//----------------------------------------------------------------------------
// NAME: ISharedChannel::SendMessage
//
// PURPOSE:
//  Sends the message object.
//
// NOTES:
//
template<typename TMessage>
void ISharedChannel::SendMessage(const TMessage& msg)
{
    // Calculate frame size.
    //
    int32_t frameLength = static_cast<int32_t>(sizeof(FrameHeader) + ObjectSerialization::GetSerializedSize(msg));
    frameLength = align<sizeof(int32_t)>(frameLength);

    // Acquire a write region to write the frame.
    //
    uint32_t writeOffset = AcquireWriteRegionForFrame(frameLength);

    if (writeOffset == std::numeric_limits<uint32_t>::max())
    {
        // The write has been terminated, ignore the send.
        //
        return;
    }

    FrameHeader& frame = Frame(writeOffset);

    // Optimization. Store the frame length with incomplete bit.
    //
    frame.Length.store(frameLength | 1, std::memory_order_release);

    // Store type index and hash.
    //
    frame.CodegenTypeIndex = TypeMetadataInfo::CodegenTypeIndex<TMessage>();
    frame.CodegenTypeHash = TypeMetadataInfo::CodegenTypeHash<TMessage>();

    // Copy the structure to the buffer.
    //
    BytePtr payload = Payload(writeOffset);
    ObjectSerialization::Serialize(payload, msg);

    // Frame is ready for the reader.
    //
    SignalFrameIsReady(frame, frameLength);

    // If there are readers in the waiting state, we need to notify them.
    //
    if (HasReadersInWaitingState())
    {
        NotifyExternalReader();
    }
}

FrameHeader& ISharedChannel::Frame(uint32_t offset)
{
    return *reinterpret_cast<FrameHeader*>(Buffer.Pointer + offset);
}

BytePtr ISharedChannel::Payload(uint32_t writeOffset)
{
    return BytePtr(Buffer.Pointer + writeOffset + sizeof(FrameHeader));
}

//----------------------------------------------------------------------------
// NAME: SharedChannel<TChannelPolicy, TChannelSpinPolicy>::AcquireWriteRegionForFrame
//
// PURPOSE:
//  Acquire a region to write the frame.
//
// RETURNS:
//  Returns an offset to acquired memory region that can hold a full frame.
//
// NOTES:
//  The acquired region is contiguous.
//
template<typename TChannelPolicy, typename TChannelSpinPolicy>
uint32_t SharedChannel<TChannelPolicy, TChannelSpinPolicy>::AcquireWriteRegionForFrame(int32_t& frameLength)
{
    const uint32_t expectedFrameLength = frameLength;

    assert(expectedFrameLength < Size);

    // Acquire writing region in the buffer.
    //
    while (true)
    {
        // Align frame length to the integer.
        // Otherwise the next frame might have unaligned offset for Length field.
        //
        frameLength = expectedFrameLength;

        // Acquire region for writes. Function might adjust frame length.
        //
        const uint32_t writeOffset = AcquireRegionForWrite(frameLength);

        if (writeOffset == std::numeric_limits<uint32_t>::max())
        {
            // The reader has terminated, abandon the write.
            //
            return writeOffset;
        }

        // We might acquired a circular region,
        // check if we can store a full frame without overlapping the buffer.
        //
        if (writeOffset + frameLength > Size)
        {
            // There is not enough space in the buffer to write the full frame.
            // Create an empty frame to adjust the write offset to the beginning of the buffer.
            // Retry the whole operation until we write a full frame.
            //
            FrameHeader& frame = Frame(writeOffset);
            frame.CodegenTypeIndex = 0;
            SignalFrameIsReady(frame, frameLength);
            continue;
        }

        // Acquired a region that we can write a full frame.
        //
        return writeOffset;
    }
}

//----------------------------------------------------------------------------
// NAME: SharedChannel<TChannelPolicy, TChannelSpinPolicy>::NotifyExternalReader
//
// PURPOSE:
//
// RETURNS:
//
// NOTES:
//
template<typename TChannelPolicy, typename TChannelSpinPolicy>
void SharedChannel<TChannelPolicy, TChannelSpinPolicy>::NotifyExternalReader()
{
    ChannelPolicy.NotifyExternalReader();
}

//----------------------------------------------------------------------------
// NAME: SharedChannel<TChannelPolicy, TChannelSpinPolicy>::AcquireRegionForWrite
//
// PURPOSE:
//  Function returns an offset to the acquired region that can we safely use for write operation.
//
// RETURNS:
//  An offset to the acquired region.
//  If reader has been aborted, return uint32_t::max.
//
// NOTES:
//  There is no guarantee that the acquired region is contiguous (it might be overlapping).
//  However it ensures that the next write offset will not be greater than the buffer margin,
//  so the next writer can write an empty FrameHeader.
//
template<typename TChannelPolicy, typename TChannelSpinPolicy>
uint32_t SharedChannel<TChannelPolicy, TChannelSpinPolicy>::AcquireRegionForWrite(int32_t& frameLength)
{
    while (true)
    {
        // FreePosition is expected to be less than WritePosition unless WritePosition has overflow.
        // To preserve this order, we read FreePosition first. Otherwise, it might advance if we had read WritePosition first.
        //
        const uint32_t freePosition = Sync.FreePosition.load(std::memory_order_acquire);
        uint32_t writePosition = Sync.WritePosition.load(std::memory_order_relaxed);

        // Check if there is enough bytes to write frame (full frame or a link).
        // Always keep the distance to free offset, at least a size of FrameHeader.
        // If WritePosition overflown, then (writePosition - freePosition) is still positive value.
        //
        if (!(writePosition - freePosition < Margin - frameLength))
        {
            // Not enough free space to acquire region.
            //

            // Check if the channel is still active.
            //
            if (Sync.TerminateChannel.load(std::memory_order_relaxed))
            {
                return std::numeric_limits<uint32_t>::max();
            }

            // Not enough free space to acquire region.
            // Advance free position to reclaim memory for writes.
            // Retry after that, as another writer might acquire just the released region.
            //
            AdvanceFreePosition();
            continue;
        }

        // If the end of the requested frame is located in the buffer margin, extend the acquired region.
        //
        int32_t frameLengthAdj = 0;

        // NextWritePosition is at the frame end.
        // NextWriteOffset (calculated from NextWritePosition) must be aligned to sizeof(uint32_t)
        // therefore frame length must be also aligned.
        //
        uint32_t nextWritePosition = writePosition + frameLength;

        // Ensure that after a full frame there is enough space for the next frame header.
        // Otherwise, we will not be able to store next frame, because the frame header will not fit in the buffer.
        //
        uint32_t nextWriteOffset = nextWritePosition % Size;
        if (nextWriteOffset >= Margin)
        {
            // Update frameLength, as we acquired more than requested.
            //
            frameLengthAdj = Size - nextWriteOffset;

            nextWritePosition += frameLengthAdj;
        }

        uint32_t expectedWritePosition = writePosition;
        if (!Sync.WritePosition.compare_exchange_weak(expectedWritePosition, nextWritePosition))
        {
            // Failed to advance write offset, other writer acquired this region.
            //
            continue;
        }

        frameLength += frameLengthAdj;

        // The region should be empty except for free links.
        // Frame links are always stored in offset aligned to sizeof int.
        //
        const uint32_t writeOffset = writePosition % Size;
        return writeOffset;
    }
}

//----------------------------------------------------------------------------
// NAME: SharedChannel<TChannelControlPolicy, TChannelSpinPolicy, TChannelWaitPolicy>::WaitForFrame
//
// PURPOSE:
//  Wait for the frame become available.
//
// RETURNS:
//  Returns an offset to the frame buffer.
//
// NOTES:
//  Reader function.
//  If the wait has been aborted, it returns uint32_t::max.
//
template<typename TChannelPolicy, typename TChannelSpinPolicy>
uint32_t SharedChannel<TChannelPolicy, TChannelSpinPolicy>::WaitForFrame()
{
    uint32_t readPosition;
    TChannelSpinPolicy channelSpinPolicy;

    bool shouldWait = false;

    while (true)
    {
        // Wait for the frame become available.
        // Spin on current frame (ReadOffset).
        //
        readPosition = Sync.ReadPosition.load(std::memory_order_acquire);

        const uint32_t readOffset = readPosition % Size;
        FrameHeader& frame = Frame(readOffset);

        int32_t frameLength = frame.Length.load(std::memory_order_relaxed);
        if (frameLength > 0)
        {
            // Writer had updated the length.
            // Frame is ready and available for the reader.
            // Advance ReadIndex to end of the frame, and allow other reads to process next frame.
            //
            uint32_t expectedReadPosition = readPosition;
            uint32_t nextReadPosition = (readPosition + (frameLength & (~1)));

            if (!Sync.ReadPosition.compare_exchange_weak(expectedReadPosition, nextReadPosition))
            {
                // Other reader advanced ReadPosition therefore it will process the frame.
                //
                channelSpinPolicy.FailedToAcquireReadRegion();
                continue;
            }

            // Current reader owns the frame. Wait untill the reader completes the write.
            //
            while ((frameLength & 1) == 1)
            {
                channelSpinPolicy.WaitForFrameCompletion();
                frameLength = frame.Length.load(std::memory_order_acquire);
            }

            break;
        }

        channelSpinPolicy.WaitForNewFrame();

        // No frame yet, spin if the channel is still active.
        //
        if (Sync.TerminateChannel.load(std::memory_order_relaxed))
        {
            return std::numeric_limits<uint32_t>::max();
        }

        // Wait for the synchronization primitive.
        //
        if (shouldWait)
        {
            ChannelPolicy.WaitForFrame();
            Sync.ReaderInWaitingStateCount.fetch_sub((uint32_t)shouldWait);
            shouldWait = false;
        }
        else
        {
            // Before reader enters wait state it will increase the in wait state count and then check if are there any messages in the channel.
            //
            shouldWait = true;
            Sync.ReaderInWaitingStateCount.fetch_add((uint32_t)shouldWait);
        }

        // If (frameLength < 0) There is active cleaning up on this frame by the writer.
        // The read offset had already advanced, so retry.
        //
    }

    // Reader acquired read region, frame is ready.
    //
    const uint32_t readOffset = readPosition % Size;

    // Reset the in wait state counter.
    //
    Sync.ReaderInWaitingStateCount.fetch_sub((uint32_t)shouldWait);

    return readOffset;
}

//----------------------------------------------------------------------------
// NAME: SharedChannel<TChannelPolicy>::WaitAndDispatchFrame
//
// PURPOSE:
//  Waits for a new frame then call proper dispatcher.
//
// RETURNS:
//  Returns true if reader successfully processed the frame.
//  If the wait has been aborted, it returns false.
//
// NOTES:
//  To interrupt wait, set Sync.TerminateReader to true.
//
template<typename TChannelPolicy, typename TChannelSpinPolicy>
bool SharedChannel<TChannelPolicy, TChannelSpinPolicy>::WaitAndDispatchFrame(
    DispatchEntry* dispatchTable,
    size_t dispatchEntryCount)
{
    const uint32_t readOffset = WaitForFrame();

    if (readOffset == std::numeric_limits<uint32_t>::max())
    {
        // Invalid offset, the wait was interrupted.
        //
        return false;
    }

    // Verify frame and call dispatcher.
    //
    FrameHeader& frame = Frame(readOffset);
    uint32_t codegenTypeIndex = frame.CodegenTypeIndex;
    uint64_t codegenTypeHash = frame.CodegenTypeHash;

    int32_t frameLength = frame.Length.load(std::memory_order_acquire);

    // Check if this is valid frame or just the link to the beginning of the buffer.
    //
    if (codegenTypeIndex != 0 && codegenTypeIndex <= dispatchEntryCount)
    {
        uint64_t expectedCodegenTypeHash = dispatchTable[codegenTypeIndex - 1].CodegenTypeHash;

        bool isMessageValid = (static_cast<uint32_t>(frameLength) < Size) && (expectedCodegenTypeHash == codegenTypeHash);

        if (isMessageValid)
        {
            // Call dispatcher only if type hash is correct.
            //
            isMessageValid = dispatchTable[codegenTypeIndex - 1].Callback(std::move(Payload(readOffset)), frameLength);
        }

        if (!isMessageValid)
        {
            // Received invalid frame, channel policy decides what how to handle it.
            //
            ChannelPolicy.ReceivedInvalidFrame();
        }

        // Cleanup. Writer requires clean memory buffer (frameLength != 0).
        // Clear the whole frame except the length.
        //
        ClearPayload(readOffset, frameLength);
    }
    else
    {
        if (codegenTypeIndex == 0)
        {
            // Just a link frame, clear the circular region.
            //
            ClearLinkPayload(readOffset, frameLength, Size);
        }
        else
        {
            // Received invalid frame, channel policy decides what how to handle it.
            //
            ChannelPolicy.ReceivedInvalidFrame();

            ClearPayload(readOffset, frameLength);
        }
    }

    // Mark frame that processing is completed (negative length).
    //
    SignalFrameForCleanup(frame, frameLength);

    return true;
}

//----------------------------------------------------------------------------
// NAME: SharedChannel<TChannelPolicy, TChannelSpinPolicy>::ProcessMessages
//
// PURPOSE:
//  Reader loop, process received messages.
//
// RETURNS:
//
// NOTES:
//
template<typename TChannelPolicy, typename TChannelSpinPolicy>
void SharedChannel<TChannelPolicy, TChannelSpinPolicy>::ProcessMessages(
    Mlos::Core::DispatchEntry* dispatchTable,
    size_t dispatchEntryCount)
{
    Sync.ActiveReaderCount.fetch_add(1);

    // Receiver thread.
    //
    bool result = true;
    while (result)
    {
        result = WaitAndDispatchFrame(dispatchTable, dispatchEntryCount);
    }

    Sync.ActiveReaderCount.fetch_sub(1);
}
}
}
