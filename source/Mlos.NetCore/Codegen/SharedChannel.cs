// -----------------------------------------------------------------------
// <copyright file="SharedChannel.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.InteropServices;

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.Core
{
    /// <summary>
    /// Communication channel synchronization object.
    /// </summary>
    /// <remarks>
    ///  It contains 3 atomic positions:
    ///  -Read
    /// - Write
    /// - Free
    /// Logically FreePosition &lt;= ReadPosition &lt;= WritePosition + Buffer.Size &lt; FreePosition.
    /// However FreePosition != WritePosition, except initial state where they are both zero.
    /// All together are used to synchronize multiple writers and readers on a single buffer.
    /// Positions are monotonic.
    /// To find the offset in the buffer from the position:
    /// Offset = Position % Buffer.Size.
    /// </remarks>
    [CodegenType]
    internal partial struct ChannelSynchronization
    {
        [Align(32)]
        internal AtomicUInt32 ReadPosition;

        [Align(32)]
        internal AtomicUInt32 WritePosition;

        [Align(32)]
        internal AtomicUInt32 FreePosition;

        /// <summary>
        /// Number of readers waiting for the notification from the external process.
        /// </summary>
        [Align(32)]
        internal AtomicUInt32 ReaderInWaitingStateCount;

        /// <summary>
        /// Current number of active readers.
        /// </summary>
        [Align(32)]
        internal AtomicUInt32 ActiveReaderCount;

        /// <summary>
        /// If true stop reading/processing messages.
        /// </summary>
        [Align(4)]
        internal AtomicBool TerminateChannel;
    }

    /// <summary>
    /// Message frame header.
    /// </summary>
    [CodegenType]
    [StructLayout(LayoutKind.Sequential, Size = FrameHeader.TypeSize)]
    public partial struct FrameHeader : IEquatable<FrameHeader>
    {
        public const int TypeSize = 16;

        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(FrameHeader left, FrameHeader right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(FrameHeader left, FrameHeader right) => !(left == right);

        /// #TODO size, not length
        ///
        /// <summary>
        /// Length of the message.
        /// </summary>
        internal AtomicInt32 Length;

        /// <summary>
        /// Index of the type serialized in the message payload.
        /// </summary>
        internal uint CodegenTypeIndex;

        /// <summary>
        /// Hash of the type.
        /// </summary>
        internal ulong CodegenTypeHash;

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is FrameHeader))
            {
                return false;
            }

            return Equals((FrameHeader)obj);
        }

        /// <inheritdoc />
        public bool Equals(FrameHeader other) =>
            Length == other.Length &&
            CodegenTypeIndex == other.CodegenTypeIndex &&
            CodegenTypeHash == other.CodegenTypeHash;

        /// <inheritdoc />
        public override int GetHashCode()
        {
            unchecked
            {
                int hash = 17;
                hash = (31 * hash) + Length.GetHashCode();
                hash = (31 * hash) + (int)CodegenTypeIndex;
                hash = (31 * hash) + (int)CodegenTypeHash;
                return hash;
            }
        }
    }

    /// <summary>
    /// Shared circular buffer channel settings.
    /// </summary>
    [CodegenConfig]
    internal partial struct ChannelSettings
    {
        /// <summary>
        /// Size of the buffer. To avoid arithmetic overflow, buffer size must be power of two.
        /// </summary>
        [ScalarSetting]
        internal int BufferSize;

        /// <summary>
        /// Number of readers using this channel.
        /// </summary>
        [ScalarSetting]
        internal int ReaderCount;
    }

    [CodegenConfig]
    internal partial class ChannelStats
    {
        [FixedSizeArray(length: 16)]
        internal readonly ChannelReaderStats[] ReaderStats;
    }

    [CodegenConfig]
    internal partial struct ChannelReaderStats
    {
        [ScalarSetting]
        internal ulong MessagesRead;

        [ScalarSetting]
        internal ulong SpinCount;
    }

    #region Control Messages

    /// <summary>
    /// Represents the message request to signal termination of the circular buffer reader thread.
    /// </summary>
    [CodegenMessage]
    internal partial struct TerminateReaderThreadRequestMessage
    {
    }

    #endregion
}
