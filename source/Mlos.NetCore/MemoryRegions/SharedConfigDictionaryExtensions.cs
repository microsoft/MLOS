// -----------------------------------------------------------------------
// <copyright file="SharedConfigDictionaryExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.Core;

namespace Proxy.Mlos.Core.Internal
{
    /// <summary>
    /// Extension method class for SharedConfigDictionary structure.
    /// </summary>
    public static class SharedConfigDictionaryExtensions
    {
        /// <summary>
        /// Initializes the shared config dictionary stored in the memory region.
        /// </summary>
        /// <param name="sharedConfigDictionary"></param>
        public static void InitializeSharedConfigDictionary(this SharedConfigDictionary sharedConfigDictionary)
        {
            uint elementCount = 2048;
            AllocationEntry allocationEntry = sharedConfigDictionary.Allocator.Allocate(default(UIntArray).CodegenTypeSize() + (sizeof(uint) * elementCount));

            sharedConfigDictionary.OffsetToConfigsArray = (uint)allocationEntry.Buffer.Offset(sharedConfigDictionary.Buffer) + (uint)default(AllocationEntry).CodegenTypeSize();

            UIntArray configsOffsetArray = sharedConfigDictionary.ConfigsOffsetArray;
            configsOffsetArray.Count = elementCount;
        }
    }

    /// <summary>
    /// Extend SharedConfigDictionary structure with custom property.
    /// </summary>
    public partial struct SharedConfigDictionary
    {
        /// <summary>
        /// Gets the config offsets array, as we allocate it dynamically.
        /// </summary>
        public UIntArray ConfigsOffsetArray => new UIntArray() { Buffer = buffer + (int)OffsetToConfigsArray };
    }
}
