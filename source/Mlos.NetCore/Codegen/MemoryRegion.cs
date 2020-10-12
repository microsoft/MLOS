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
    /// Registered shared memory region.
    /// </summary>
    [CodegenType]
    public partial struct RegisteredMemoryRegionConfig
    {
        [ScalarSetting(isPrimaryKey: true)]
        internal uint MemoryRegionIndex;

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
}
