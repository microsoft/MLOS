// -----------------------------------------------------------------------
// <copyright file="MemoryRegion.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.Core.Internal
{
    /// <summary>
    /// Memory region type.
    /// </summary>
    public enum MemoryRegionType : ushort
    {
        /// <summary>
        /// Global (main) memory region.
        /// </summary>
        Global = 1,

        /// <summary>
        /// Memory region is used exclusively for the shared control channel.
        /// </summary>
        ControlChannel = 2,

        /// <summary>
        /// Memory region is used exclusively for the shared feedback channel.
        /// </summary>
        FeedbackChannel = 3,

        /// <summary>
        /// Region is used to store shared configurations.
        /// </summary>
        SharedConfig = 4,
    }

    /// <summary>
    /// Memory region identifier.
    /// </summary>
    [CodegenType]
    public partial struct MemoryRegionId : IEquatable<MemoryRegionId>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(MemoryRegionId left, MemoryRegionId right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(MemoryRegionId left, MemoryRegionId right) => !(left == right);

        /// <summary>
        /// Memory region type.
        /// </summary>
        public MemoryRegionType Type;

        /// <summary>
        /// Region Index.
        /// </summary>
        /// <remarks>
        /// Default 0.
        /// </remarks>
        public ushort Index;

        /// <inheritdoc />
        public override bool Equals(object obj)
        {
            if (!(obj is MemoryRegionId))
            {
                return false;
            }

            return Equals((MemoryRegionId)obj);
        }

        /// <inheritdoc />
        public bool Equals(MemoryRegionId other) => Type == other.Type && Index == other.Index;

        /// <inheritdoc />
        public override int GetHashCode() => (((ulong)Type << 16) + Index).GetHashCode();
    }

    /// <summary>
    /// Definition of memory region.
    /// </summary>
    [CodegenType]
    internal partial struct MemoryRegion
    {
        /// <summary>
        /// Size of the memory region.
        /// </summary>
        internal ulong MemoryRegionSize;

        /// <summary>
        /// Memory region signature.
        /// </summary>
        /// <remarks>
        /// Allows to identify the memory region by external application.
        /// </remarks>
        internal uint Signature;

        /// <summary>
        /// CodeType identifier of the memory region.
        /// </summary>
        internal uint MemoryRegionCodeTypeIndex;

        /// <summary>
        /// Memory region identifier.
        /// </summary>
        internal MemoryRegionId MemoryRegionId;
    }

    /// <summary>
    /// Registered shared memory region.
    /// </summary>
    [CodegenType]
    public partial struct RegisteredMemoryRegionConfig
    {
        [ScalarSetting(isPrimaryKey: true)]
        internal MemoryRegionType MemoryRegionType;

        [ScalarSetting(isPrimaryKey: true)]
        internal ushort MemoryRegionIndex;

        /// <summary>
        /// Name of the shared memory map.
        /// </summary>
        [ScalarSetting]
        internal StringPtr SharedMemoryMapName;

        /// <summary>
        /// Size of the memory region.
        /// </summary>
        internal ulong MemoryRegionSize;
    }

    /// <summary>
    /// Message used to exchange file descriptor via Unix domain socket.
    /// </summary>
    [CodegenType]
    public partial struct FileDescriptorExchangeMessage
    {
        /// <summary>
        /// Memory region identifier.
        /// </summary>
        public MemoryRegionId MemoryRegionId;

        /// <summary>
        /// Indicates whether message contains a valid file descriptor.
        /// </summary>
        public bool ContainsFd;

        /// <summary>
        /// Size of the memory region.
        /// </summary>
        public ulong MemoryRegionSize;
    }
}
