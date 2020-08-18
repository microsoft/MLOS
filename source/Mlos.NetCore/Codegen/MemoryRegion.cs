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
        /// Code type identifier of the memory region.
        /// </summary>
        internal uint MemoryRegionCodeTypeIndex;

        /// <summary>
        /// Region memory identifier.
        /// </summary>
        internal uint MemoryRegionId;
    }

    /// <summary>
    /// Defines address of the object in the memory region.
    /// </summary>
    [CodegenType]
    internal partial struct MemoryAddress : IEquatable<MemoryAddress>
    {
        /// <summary>
        /// Operator ==.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator ==(MemoryAddress left, MemoryAddress right) => left.Equals(right);

        /// <summary>
        /// Operator !=.
        /// </summary>
        /// <param name="left"></param>
        /// <param name="right"></param>
        /// <returns></returns>
        public static bool operator !=(MemoryAddress left, MemoryAddress right) => !(left == right);

        /// <inheritdoc/>
        public override bool Equals(object obj)
        {
            if (!(obj is MemoryAddress))
            {
                return false;
            }

            return Equals((MemoryAddress)obj);
        }

        /// <inheritdoc/>
        public bool Equals(MemoryAddress other) =>
            MemoryRegionId == other.MemoryRegionId &&
            Offset == other.Offset;

        /// <inheritdoc/>
        public override int GetHashCode() => base.GetHashCode();

        /// <summary>
        /// Id of the shared memory region.
        /// </summary>
        internal uint MemoryRegionId;

        /// <summary>
        /// Offset from the beginning of the memory region.
        /// </summary>
        internal uint Offset;
    }

    /// <summary>
    /// Request message to register memory region.
    /// </summary>
    [CodegenMessage]
    internal partial struct RegisterMemoryRegionRequestMessage
    {
        /// <summary>
        /// Shared memory name.
        /// </summary>
        internal StringPtr Name;

        /// <summary>
        /// Size of the memory region.
        /// </summary>
        internal ulong MemoryRegionSize;

        /// <summary>
        /// Region memory identifier.
        /// </summary>
        internal uint MemoryRegionId;
    }
}