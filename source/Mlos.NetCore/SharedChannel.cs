// -----------------------------------------------------------------------
// <copyright file="SharedChannel.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.CompilerServices;

using MlosProxy = Proxy.Mlos.Core;
using StdTypesProxy = Proxy.Mlos.SettingsSystem.StdTypes;

namespace Mlos.Core
{
    /// <summary>
    /// Shared channel interface.
    /// </summary>
    public interface ISharedChannel
    {
        /// <summary>
        /// Send the message object.
        /// </summary>
        /// <typeparam name="TMessage">Type of the message to be send.</typeparam>
        /// <param name="msg"></param>
        void SendMessage<TMessage>(ref TMessage msg)
            where TMessage : ICodegenType;

        /// <summary>
        /// Reader loop, process received messages.
        /// </summary>
        /// <param name="dispatchTable"></param>
        void ProcessMessages(ref DispatchEntry[] dispatchTable);

        /// <summary>
        /// Gets channel synchronization object.
        /// </summary>
        internal MlosProxy.ChannelSynchronization SyncObject { get; }
    }

    /// <summary>
    /// Shared channel.
    /// Exchange protocol based on circular buffer.
    /// More details in: Doc/CircularBuffer.md.
    /// </summary>
    /// <typeparam name="TChannelPolicy">Shared channel policy.</typeparam>
    /// <typeparam name="TChannelSpinPolicy">Shared channel spin policy.</typeparam>
    public class SharedChannel<TChannelPolicy, TChannelSpinPolicy> : ISharedChannel
        where TChannelPolicy : ISharedChannelPolicy
        where TChannelSpinPolicy : ISharedChannelSpinPolicy
    {
        /// <summary>
        /// ZeroMemory.
        /// </summary>
        /// <param name="dest"></param>
        /// <param name="count"></param>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static void ZeroMemory(IntPtr dest, int count)
        {
            unsafe
            {
                for (int i = 0; i < count; i++)
                {
                    *(byte*)(dest + i) = 0;
                }
            }
        }

        /// <summary>
        /// Signals readers that the frame is available to process.
        /// </summary>
        /// <param name="frame"></param>
        /// <param name="frameLength"></param>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        internal static void SignalFrameIsReady(
            MlosProxy.FrameHeader frame,
            int frameLength)
        {
            frame.Length.Store(frameLength);
        }

        /// <summary>
        /// Notify the cleanup thread, that the frame has been processed.
        /// </summary>
        /// <param name="frame"></param>
        /// <param name="frameLength"></param>
        /// <remarks>Reader function.</remarks>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        internal static void SignalFrameForCleanup(MlosProxy.FrameHeader frame, int frameLength)
        {
            frame.Length.Store(-frameLength);
        }

        /// <summary>
        /// Follows the free links until we reach the current read position.
        /// </summary>
        /// <remarks>
        /// While we follow the links, the method is not cleaning the memory.
        /// The memory is cleared by the reader after processing the frame.
        /// The whole memory region is clean except locations where negative frame length values are stored
        /// to signal that the message has been read and the frame is free-able.
        /// Those locations are always aligned to the size of uint32_t. The current reader continues to spin if it reads negative frame length.
        /// </remarks>
        internal void AdvanceFreePosition()
        {
            // Create AtomicUInt32 proxies once.
            //
            StdTypesProxy.AtomicUInt32 atomicFreePosition = Sync.FreePosition;
            StdTypesProxy.AtomicUInt32 atomicReadPosition = Sync.ReadPosition;

            // Move free position and allow the writer to advance.
            //
            uint freePosition = atomicFreePosition.Load();
            uint readPosition = atomicReadPosition.LoadRelaxed();

            if (freePosition == readPosition)
            {
                // Free position points to the current read position.
                //
                return;
            }

            // For diagnostic purposes, by following the free links, we should get the same distance.
            //
            uint distance = readPosition - freePosition;

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
                uint freeOffset = freePosition % Size;

                MlosProxy.FrameHeader frame = Frame(freeOffset);
                int frameLength = frame.Length.Load();

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
                uint expectedFreePosition = freePosition;
                uint nextFreePosition = freePosition - (uint)frameLength;

                if (atomicFreePosition.LoadRelaxed() != expectedFreePosition ||
                    atomicFreePosition.CompareExchange(nextFreePosition, expectedFreePosition) != expectedFreePosition)
                {
                    // Advanced by another writer, local free offset is now the write region.
                    //
                    return;
                }

                freePosition = nextFreePosition;

                // Frame length is negative.
                //
                distance += (uint)frameLength;
            }
        }

        /// <summary>
        /// Function returns an offset to the acquired region that can we safely use for write operation.
        /// </summary>
        /// <param name="frameLength"></param>
        /// <returns>
        /// An offset to the acquired region.
        /// If reader has been aborted, return uint32_t::max.
        /// </returns>
        /// <remarks>
        ///  There is no guarantee that the acquired region is contiguous (it might be overlapping).
        ///  However it ensures that the next write offset will not be greater than the buffer margin,
        ///  so the next writer can write an empty FrameHeader.
        /// </remarks>
        private uint AcquireRegionForWrite(ref int frameLength)
        {
            // Create AtomicUInt32 proxies once.
            //
            StdTypesProxy.AtomicUInt32 atomicFreePosition = Sync.FreePosition;
            StdTypesProxy.AtomicUInt32 atomicWritePosition = Sync.WritePosition;
            StdTypesProxy.AtomicBool atomicTerminateChannel = Sync.TerminateChannel;

            TChannelSpinPolicy channelSpinPolicy = default;

            while (true)
            {
                // FreePosition is expected to be less than WritePosition unless WritePosition has overflow.
                // To preserve this order, we read FreePosition first. Otherwise, it might advance if we had read WritePosition first.
                //
                uint freePosition = atomicFreePosition.Load();
                uint writePosition = atomicWritePosition.LoadRelaxed();

                // Check if there is enough bytes to write frame (full frame or a link).
                // Always keep the distance to free offset, at least a size of FrameHeader.
                // If WritePosition overflown, then (writePosition - freePosition) is still positive value.
                //
                if (!(writePosition - freePosition < margin - frameLength))
                {
                    // Not enough free space to acquire region.
                    //

                    // Check if the channel is still active.
                    //
                    if (atomicTerminateChannel.LoadRelaxed())
                    {
                        return uint.MaxValue;
                    }

                    // Advance free position to reclaim memory for writes.
                    // Retry after that, as another writer might acquire just the released region.
                    //
                    AdvanceFreePosition();
                    continue;
                }

                // If the end of the requested frame is located in the buffer margin, extend the acquired region.
                //
                uint frameLengthAdj = 0;

                // NextWritePosition is at the frame end.
                // NextWriteOffset (calculated from NextWritePosition) must be aligned to sizeof(uint32_t)
                // therefore frame length must be also aligned.
                //
                uint nextWritePosition = (uint)(writePosition + frameLength);

                // Ensure that after a full frame there is enough space for the next frame header.
                // Otherwise, we will not be able to store next frame, because the frame header will not fit in the buffer.
                //
                uint nextWriteOffset = nextWritePosition % Size;
                if (nextWriteOffset >= margin)
                {
                    // Update frameLength, as we acquired more than requested.
                    //
                    frameLengthAdj = Size - nextWriteOffset;

                    nextWritePosition += frameLengthAdj;
                }

                uint expectedWritePosition = writePosition;
                if (atomicWritePosition.LoadRelaxed() != expectedWritePosition ||
                    atomicWritePosition.CompareExchange(nextWritePosition, expectedWritePosition) != expectedWritePosition)
                {
                    // Failed to advance write offset, another writer acquired this region.
                    //
                    channelSpinPolicy.FailedToAcquireWriteRegion();
                    continue;
                }

                frameLength += (int)frameLengthAdj;

                // The region should be empty except for free links.
                // Frame links are always stored in offset aligned to sizeof int.
                //
                uint writeOffset = writePosition % Size;
                return writeOffset;
            }
        }

        /// <summary>
        /// Acquire a region to write the frame.
        /// </summary>
        /// <param name="frameLength"></param>
        /// <returns>Returns an offset to acquired memory region that can hold a full frame.</returns>
        /// <remarks>The acquired region is contiguous.</remarks>
        internal uint AcquireWriteRegionForFrame(ref int frameLength)
        {
            uint expectedFrameLength = (uint)frameLength;

            // Acquire writing region in the buffer.
            //
            while (true)
            {
                // Align frame length to the integer.
                // Otherwise the next frame might have unaligned offset for Length field.
                //
                frameLength = (int)expectedFrameLength;

                // Acquire region for writes. Function might adjust frame length.
                //
                uint writeOffset = AcquireRegionForWrite(ref frameLength);

                if (writeOffset == uint.MaxValue)
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
                    MlosProxy.FrameHeader frame = Frame(writeOffset);
                    frame.CodegenTypeIndex = 0;
                    SignalFrameIsReady(frame, frameLength);
                    continue;
                }

                // Acquired a region that we can write a full frame.
                //
                return writeOffset;
            }
        }

        /// <summary>
        /// Wait for the frame become available.
        /// </summary>
        /// <returns>Returns an offset to the frame buffer.</returns>
        /// <remarks>
        /// Reader function.
        /// If the wait has been aborted, it returns uint32_t::max.
        /// </remarks>
        internal uint WaitForFrame()
        {
            uint readPosition;
            TChannelSpinPolicy channelSpinPolicy = default;

            // Create AtomicUInt32 proxy once.
            //
            StdTypesProxy.AtomicUInt32 atomicReadPosition = Sync.ReadPosition;
            StdTypesProxy.AtomicUInt32 atomicReaderInWaitingStateCount = Sync.ReaderInWaitingStateCount;
            StdTypesProxy.AtomicBool atomicTerminateChannel = Sync.TerminateChannel;

            MlosProxy.FrameHeader frame = default;

            uint shouldWait = 0;

            // int spinIndex = 0;
            while (true)
            {
                // Wait for the frame become available.
                // Spin on current frame (ReadOffset).
                //
                readPosition = atomicReadPosition.Load();

                uint readOffset = readPosition % Size;
                frame = Frame(readOffset);

                int frameLength = frame.Length.Load();
                if (frameLength > 0)
                {
                    // Writer had updated the length.
                    // Frame is ready and available for the reader.
                    // Advance ReadIndex to end of the frame, and allow other reads to process next frame.
                    //
                    uint expectedReadPosition = readPosition;
                    uint nextReadPosition = readPosition + (uint)(frameLength & (~1));

                    if (atomicReadPosition.LoadRelaxed() != expectedReadPosition ||
                        atomicReadPosition.CompareExchange(nextReadPosition, expectedReadPosition) != expectedReadPosition)
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
                        frameLength = frame.Length.Load();
                    }

                    if (frameLength > 0)
                    {
                        break;
                    }

                    // Frame might have been cleared.
                    //
                    continue;
                }

                channelSpinPolicy.WaitForNewFrame();

                // if ((++spinIndex & 0xff) == 0)
                {
                    // No frame yet, spin if the channel is stil active.
                    //
                    if (atomicTerminateChannel.LoadRelaxed())
                    {
                        return uint.MaxValue;
                    }
                }

                // Wait for the synchronization primitive.
                //
                if (shouldWait != 0)
                {
                    ChannelPolicy.WaitForFrame();
                    atomicReaderInWaitingStateCount.FetchSub(shouldWait);
                    shouldWait = 0;
                }
                else
                {
                    // Before reader enters wait state it will increase ReaderInWaitingState count and then check if are there any messages in the channel.
                    //
                    shouldWait = 1;
                    atomicReaderInWaitingStateCount.FetchAdd(shouldWait);
                }

                // If (frameLength < 0) there is active cleaning up on this frame by the writer.
                // The read offset had already advanced, so retry.
                //
            }

            // Reset InWaitingState counter.
            //
            atomicReaderInWaitingStateCount.FetchSub(shouldWait);

            // Reader acquired read region, frame is ready.
            //
            return readPosition % Size;
        }

        /// <summary>
        /// Waits for a new frame then call proper dispatcher.
        /// </summary>
        /// <param name="dispatchTable"></param>
        /// <returns>
        /// Returns true if reader successfully processed the frame. If the wait has been aborted, it returns false.
        /// </returns>
        /// <remarks>
        /// To interrupt wait, set buffer.Sync.TerminateReader to true.
        /// </remarks>
        public bool WaitAndDispatchFrame(DispatchEntry[] dispatchTable)
        {
            TChannelPolicy channelPolicy = default;

            uint readOffset = WaitForFrame();

            if (readOffset == uint.MaxValue)
            {
                // Invalid offset, the wait was interrupted.
                //
                return false;
            }

            uint dispatchEntryCount = (uint)dispatchTable.Length;

            // Verify frame and call dispatcher.
            //
            MlosProxy.FrameHeader frame = Frame(readOffset);
            uint codegenTypeIndex = frame.CodegenTypeIndex;
            ulong codegenTypeHash = frame.CodegenTypeHash;

            int frameLength = frame.Length.LoadRelaxed();

            // Check if this is valid frame or just the link to the beginning of the buffer.
            //
            if (codegenTypeIndex != 0 && codegenTypeIndex <= dispatchEntryCount)
            {
                // Use hash to check the message.
                //
                ulong expectedCodegenTypeHash = dispatchTable[codegenTypeIndex - 1].CodegenTypeHash;

                bool isMessageValid = ((uint)frameLength < Size) && (expectedCodegenTypeHash == codegenTypeHash);

                if (isMessageValid)
                {
                    unsafe
                    {
                        // Call dispatcher only if type hash is correct.
                        //
                        isMessageValid = dispatchTable[codegenTypeIndex - 1].Callback(Payload(readOffset), frameLength);
                    }
                }

                if (!isMessageValid)
                {
                    // Received invalid frame, channel policy decides what how to handle it.
                    //
                    channelPolicy.ReceivedInvalidFrame();
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
                    channelPolicy.ReceivedInvalidFrame();

                    ClearPayload(readOffset, frameLength);
                }
            }

            // Mark frame that processing is completed (negative length).
            //
            SignalFrameForCleanup(frame, frameLength);

            return true;
        }

        /// <inheritdoc/>
        public void ProcessMessages(ref DispatchEntry[] dispatchTable)
        {
            Sync.TerminateChannel.Store(false);

            Sync.ActiveReaderCount.FetchAdd(1);

            // Receiver thread.
            //
            bool result = true;
            while (result)
            {
              result = WaitAndDispatchFrame(dispatchTable);
            }

            Sync.ActiveReaderCount.FetchSub(1);
        }

        /// <inheritdoc/>
        public void SendMessage<TMessage>(ref TMessage msg)
            where TMessage : ICodegenType
        {
            // Calculate frame size.
            //
            int frameLength = FrameHeader.TypeSize + (int)CodegenTypeExtensions.GetSerializedSize(msg);
            frameLength = Utils.Align(frameLength, sizeof(int));

            // Acquire a write region to write the frame.
            //
            uint writeOffset = AcquireWriteRegionForFrame(ref frameLength);

            if (writeOffset == uint.MaxValue)
            {
                // The write has been interrupted.
                //
                return;
            }

            MlosProxy.FrameHeader frame = Frame(writeOffset);

            // Optimization. Store the frame length with incomplete bit.
            //
            frame.Length.Store(frameLength | 1);

            // Store type index and hash.
            //
            frame.CodegenTypeIndex = msg.CodegenTypeIndex();
            frame.CodegenTypeHash = msg.CodegenTypeHash();

            // Copy the structure to the buffer.
            //
            IntPtr payload = Payload(writeOffset);
            CodegenTypeExtensions.Serialize(msg, payload);

            // Frame is ready for the reader.
            //
            SignalFrameIsReady(frame, frameLength);

            // If there are readers in the waiting state, we need to notify them.
            //
            if (HasReadersInWaitingState())
            {
                ChannelPolicy.NotifyExternalReader();
            }
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="SharedChannel{TChannelPolicy, TChannelSpinPolicy}"/> class.
        /// Constructor.
        /// </summary>
        /// <param name="sharedMemoryMapView"></param>
        /// <param name="sync"></param>
        public SharedChannel(SharedMemoryMapView sharedMemoryMapView, MlosProxy.ChannelSynchronization sync)
            : this(sharedMemoryMapView.Buffer, (uint)sharedMemoryMapView.MemSize, sync)
        {
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="SharedChannel{TChannelPolicy, TChannelSpinPolicy}"/> class.
        /// Constructor.
        /// </summary>
        /// <param name="buffer"></param>
        /// <param name="size"></param>
        /// <param name="sync"></param>
        public SharedChannel(IntPtr buffer, uint size, MlosProxy.ChannelSynchronization sync)
        {
            Sync = sync;

            unsafe
            {
                // Buffset size requirements:
                // - Buffer size must be aligned to sizeof(uint32_t).
                // - To handle position (uint32_t) overflow,
                //    Size of the buffer must satisfy the following condition:
                //    uint32_t.max +1 % Buffer.Size == 0.
                //
                Buffer = buffer;
                Size = size;
                margin = Size - (uint)sizeof(FrameHeader);
            }

            // Initialize channel.
            //
            InitializeChannel();
        }

        /// <summary>
        /// Initializes the shared channel.
        /// </summary>
        /// <remarks>
        /// The method handles the failures when one of the processes has terminated unexpectedly.
        /// </remarks>
        private void InitializeChannel()
        {
            Sync.TerminateChannel.Store(false);

            // Recover from the previous failures.
            //

            // Advance free region. Follow the free links up to a current read position.
            //
            AdvanceFreePosition();

            // We reached first unprocessed frame. Follow the frames untill we reach writePosition.
            // Clear the partially written frames and convert processed frames into empty ones, so the reader can ignore them.
            //
            uint freePosition = Sync.FreePosition.Load();
            uint writePosition = Sync.WritePosition.LoadRelaxed();

            while (freePosition != writePosition)
            {
                // Check the current state of the frame by inspecting it's length.
                //
                uint freeOffset = freePosition % Size;
                MlosProxy.FrameHeader frame = Frame(freeOffset);

                int frameLength = frame.Length.Load();

                if (frameLength < 0 || (frameLength & 1) == 1)
                {
                    // The frame has been processed or the frame has been partially written.
                    //
                    frameLength = frameLength > 0 ? frameLength : -frameLength;
                    frameLength &= ~1;

                    // The frame is partially written. Ignore it.
                    //
                    ClearPayload(freeOffset, frameLength);

                    frame.Length.Store(frameLength);
                }

                // Move to next frame.
                //
                freePosition += (uint)frameLength;
            }

            // Set readPosition to freePostion to reprocess the frames.
            //
            freePosition = Sync.FreePosition.Load();
            uint readPosition = Sync.ReadPosition.Load();
            Sync.ReadPosition.CompareExchange(freePosition, readPosition);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private void ClearPayload(uint writeOffset, int frameLength)
        {
            ZeroMemory(Buffer + (int)writeOffset + sizeof(uint), frameLength - sizeof(uint));
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private void ClearLinkPayload(uint writeOffset, int frameLength, uint bufferSize)
        {
            writeOffset += sizeof(uint);
            frameLength -= sizeof(uint);

            if (writeOffset + frameLength > bufferSize)
            {
                // Overlapped link.
                //
                ZeroMemory(Buffer + (int)writeOffset, (int)(bufferSize - writeOffset));
                ZeroMemory(Buffer, frameLength + (int)(writeOffset - bufferSize));
            }
            else
            {
                ZeroMemory(Buffer + (int)writeOffset, frameLength);
            }
        }

        /// <summary>
        /// Size of the buffer - sizeof(FrameHeader).
        /// </summary>
        private readonly uint margin;

        /// <summary>
        /// Channel synchronization object.
        /// </summary>
        internal MlosProxy.ChannelSynchronization Sync;

        /// <summary>
        /// Pointer to the shared memory.
        /// </summary>
        internal IntPtr Buffer;

        /// <summary>
        /// Gets the message frame at given offset.
        /// </summary>
        /// <param name="freeOffset"></param>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        internal MlosProxy.FrameHeader Frame(uint freeOffset)
        {
            unsafe
            {
                return new MlosProxy.FrameHeader() { Buffer = Buffer + (int)freeOffset };
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        internal IntPtr Payload(uint offset)
        {
            unsafe
            {
                return Buffer + (int)offset + sizeof(FrameHeader);
            }
        }

        /// <summary>
        /// Returns true if there are reader threads waiting for external process.
        /// </summary>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        internal bool HasReadersInWaitingState()
        {
            return Sync.ReaderInWaitingStateCount.Load() != 0;
        }

        /// <summary>
        /// Size of the buffer.
        /// </summary>
        public uint Size;

        /// <summary>
        /// Channel control policy.
        /// </summary>
        public TChannelPolicy ChannelPolicy;

        /// <inheritdoc/>
        MlosProxy.ChannelSynchronization ISharedChannel.SyncObject => Sync;
    }
}
