//*********************************************************************
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See License.txt in the project root
// for license information.
//
// @File: SharedChannel.cpp
//
// Purpose:
//  Exchange protocol based on circular buffer.
//
//
// Notes:
//  More details in: Doc/CircularBuffer.md.
//
//*********************************************************************

#include "Mlos.Core.h"

namespace Mlos
{
namespace Core
{
//----------------------------------------------------------------------------
// NAME: SignalFrameIsReady
//
// PURPOSE:
//  Signals readers that the frame is available to process.
//
// RETURNS:
//
// NOTES:
//
void SignalFrameIsReady(FrameHeader& frame, int32_t frameLength)
{
    frame.Length.store(frameLength, std::memory_order_release);
}

//----------------------------------------------------------------------------
// NAME: SignalFrameForCleanup
//
// PURPOSE:
//  Notify the cleanup thread, that the frame has been processed.
//
// RETURNS:
//  Nothing.
//
// NOTES:
//  Reader function.
//
void SignalFrameForCleanup(FrameHeader& frame, int32_t frameLength)
{
    frame.Length.store(-frameLength, std::memory_order_release);
}

//----------------------------------------------------------------------------
// NAME: ISharedChannel::InitializeChannel
//
// PURPOSE:
//  The method handles the failures when one of the processes has terminated unexpectedly.
//
// RETURNS:
//  Nothing.
//
// NOTES:
//
void ISharedChannel::InitializeChannel()
{
    Sync.TerminateChannel.store(false);

    // Recover from the previous failures.
    //

    // Advance the free region. Follow the free links up to the current read position.
    //
    AdvanceFreePosition();

    // We reached first unprocessed frame. Follow the frames untill we reach writePosition.
    // Clear the partially written frames and convert processed frames into empty ones, so the reader can ignore them.
    //
    uint32_t freePosition = Sync.FreePosition.load(std::memory_order_acquire);
    uint32_t writePosition = Sync.WritePosition.load(std::memory_order_relaxed);

    while (freePosition != writePosition)
    {
        // Check the current state of the frame by inspecting it's length.
        //
        const uint32_t freeOffset = freePosition % Size;
        FrameHeader& frame = Frame(freeOffset);

        int32_t frameLength = frame.Length.load(std::memory_order_acquire);

        if (frameLength < 0 || (frameLength & 1) == 1)
        {
            // The frame has been processed or the frame has been partially written.
            //
            //
            frameLength = frameLength > 0 ? frameLength : -frameLength;
            frameLength &= ~1;

            // The frame is partially written. Ignore it.
            //
            ClearPayload(freeOffset, frameLength);

            frame.Length.store(frameLength, std::memory_order_release);
        }

        // Move to next frame.
        //
        freePosition += frameLength;
    }

    // Set readPosition to freePostion to reprocess the frames.
    //
    freePosition = Sync.FreePosition.load(std::memory_order_acquire);
    uint32_t readPosition = Sync.ReadPosition.load(std::memory_order_acquire);
    Sync.ReadPosition.compare_exchange_strong(readPosition, freePosition);
}

//----------------------------------------------------------------------------
// NAME: ISharedChannel::AdvanceFreePosition
//
// PURPOSE:
//  Follows the free links until we reach the read position.
//
// RETURNS: None.
//
// NOTES:
//  While we follow the links, the method is not cleaning the memory.
//  The memory is cleared by the reader after processing the frame.
//  The whole memory region is clean except locations where negative frame length values are stored
//  to signal that the message has been read and the frame is free-able.
//  Those locations are always aligned to the size of uint32_t. The current reader continues to spin if it reads negative frame length.
//
void ISharedChannel::AdvanceFreePosition()
{
    // Move free position and allow the writer to advance.
    //
    uint32_t freePosition = Sync.FreePosition.load(std::memory_order_acquire);
    uint32_t readPosition = Sync.ReadPosition.load(std::memory_order_relaxed);

    if (freePosition == readPosition)
    {
        // Free position points to the current read position.
        //
        return;
    }

    // For diagnostic purposes, following the free links we should get the same distance.
    //
    uint32_t distance = readPosition - freePosition;

    // Follow the free links up to the current read position.
    // The cleanup is completed when the free position is equal to the read position.
    // However, by the time this cleanup is completed, the reader threads might process more frames and advance the read position.
    //
    while (freePosition != readPosition)
    {
        // Load a frame from the beginning of the free region.
        // However, other writer threads might already advance the free position.
        // In this case, local free position points to the write region and
        // we will fail to advance free offset.
        //
        const uint32_t freeOffset = freePosition % Size;
        const FrameHeader& frame = Frame(freeOffset);
        int32_t frameLength = frame.Length.load(std::memory_order_acquire);

        if (frameLength >= 0)
        {
            // Frame is currently processed or has been already cleared.
            // Other writer thread advanced free position, there is no point to check using compare_exchange_weak.
            // Local free offset is now the write region.
            //
            return;
        }

        // Advance free position. The frame length is negative.
        //
        uint32_t expectedFreePosition = freePosition;
        uint32_t nextFreePosition = (freePosition - frameLength);

        if (!Sync.FreePosition.compare_exchange_weak(expectedFreePosition, nextFreePosition))
        {
            // Advanced by another writer, local free offset is now the write region.
            //
            return;
        }

        freePosition = nextFreePosition;

        // Frame length is negative.
        //
        distance += frameLength;
    }

    assert(distance == 0);
}
}
}
