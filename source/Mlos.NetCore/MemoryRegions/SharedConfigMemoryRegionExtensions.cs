// -----------------------------------------------------------------------
// <copyright file="SharedConfigMemoryRegionExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.Core;
using Mlos.Core.Collections;

namespace Proxy.Mlos.Core.Internal
{
    public static class SharedConfigMemoryRegionExtensions
    {
        public static AllocationEntry Allocate(this SharedConfigMemoryRegion sharedConfigMemoryRegion, ulong size)
        {
            size += default(AllocationEntry).CodegenTypeSize();

            var allocator = sharedConfigMemoryRegion.Allocator;

            if (allocator.FreeOffset + size >= sharedConfigMemoryRegion.MemoryHeader.MemoryRegionSize)
            {
                throw new OutOfMemoryException();
            }

            // Update the address.
            //
            uint offset = allocator.FreeOffset;

            // Update memory region properties.
            //
            allocator.FreeOffset += (uint)Utils.Align(size, 64);
            allocator.AllocationCount++;

            // Update last allocated entry.
            //
            if (allocator.LastAllocatedOffset != 0)
            {
                AllocationEntry lastAllocationEntry = new AllocationEntry() { Buffer = sharedConfigMemoryRegion.Buffer + (int)allocator.LastAllocatedOffset };

                lastAllocationEntry.NextEntryOffset = offset;
            }

            // Update current allocated entry.
            //
            AllocationEntry allocationEntry = new AllocationEntry() { Buffer = sharedConfigMemoryRegion.Buffer + (int)offset };
            allocationEntry.PrevEntryoffset = allocator.LastAllocatedOffset;

            allocator.LastAllocatedOffset = offset;

            return allocationEntry;
        }

        public static T Allocate<T>(this SharedConfigMemoryRegion sharedConfigMemoryRegion)
            where T : ICodegenProxy, new()
        {
            AllocationEntry allocationEntry = sharedConfigMemoryRegion.Allocate(default(T).CodegenTypeSize());

            T codegenProxy = new T() { Buffer = allocationEntry.Buffer + (int)default(AllocationEntry).CodegenTypeSize() };

            return codegenProxy;
        }

        /// <summary>
        /// Internal lookup. TProxy type is deduced by the caller.
        /// </summary>
        /// <typeparam name="TProbingPolicy">HashTable lookup policy.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy type.</typeparam>
        /// <param name="sharedConfigMemoryRegion"></param>
        /// <param name="codegenKey"></param>
        /// <param name="slotIndex"></param>
        /// <returns></returns>
        public static SharedConfig<TProxy> Get<TProbingPolicy, TProxy>(
            this SharedConfigMemoryRegion sharedConfigMemoryRegion,
            ICodegenKey codegenKey,
            ref uint slotIndex)
            where TProbingPolicy : IProbingPolicy
            where TProxy : ICodegenProxy, new()
        {
            TProbingPolicy probingPolicy = default;

            uint probingCount = 0;
            slotIndex = 0;

            var configsArray = new UIntArray() { Buffer = sharedConfigMemoryRegion.Buffer + (int)sharedConfigMemoryRegion.ConfigsArrayOffset };

            uint elementCount = configsArray.Count;
            ProxyArray<uint> sharedConfigsOffsets = configsArray.Elements;

            SharedConfig<TProxy> sharedConfig = default;

            while (true)
            {
                slotIndex = probingPolicy.CalculateIndex(codegenKey, ref probingCount, elementCount);

                uint sharedConfigOffsets = sharedConfigsOffsets[(int)slotIndex];

                if (sharedConfigOffsets == 0)
                {
                    // Slot entry is empty.
                    //
                    sharedConfig.Buffer = IntPtr.Zero;
                    break;
                }

                // Compare the object keys.
                // Create a proxy to the shared config.
                //
                sharedConfig.Buffer = sharedConfigMemoryRegion.Buffer + (int)sharedConfigOffsets;

                // Compare key with the proxy.
                //
                bool foundEntry = codegenKey.CodegenTypeIndex() == sharedConfig.Header.CodegenTypeIndex
                    && codegenKey.CompareKey(sharedConfig.Config);
                if (foundEntry)
                {
                    break;
                }

                ++probingCount;
            }

            return sharedConfig;
        }

        /// <summary>
        /// Add a new shared config.
        /// </summary>
        /// <typeparam name="TProbingPolicy">HashTable lookup policy.</typeparam>
        /// <typeparam name="TType">Codegen config type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy type.</typeparam>
        /// <param name="sharedConfigMemoryRegion"></param>
        /// <param name="componentConfig"></param>
        public static void Add<TProbingPolicy, TType, TProxy>(
            this SharedConfigMemoryRegion sharedConfigMemoryRegion,
            ComponentConfig<TType, TProxy> componentConfig)
            where TProbingPolicy : IProbingPolicy
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;

            SharedConfig<TProxy> sharedConfig = sharedConfigMemoryRegion.Get<TProbingPolicy, TProxy>(componentConfig.Config, ref slotIndex);

            if (sharedConfig.Buffer != IntPtr.Zero)
            {
                throw new ArgumentException("Config already present", nameof(componentConfig));
            }

            TType config = componentConfig.Config;

            // Calculate size to allocate.
            //
            sharedConfig = sharedConfigMemoryRegion.Allocate<SharedConfig<TProxy>>();

            // Update hash map
            //
            ProxyArray<uint> sharedConfigOffsets = sharedConfigMemoryRegion.ConfigsOffsetArray.Elements;

            sharedConfigOffsets[(int)slotIndex] = (uint)sharedConfig.Buffer.Offset(sharedConfigMemoryRegion.Buffer);

            // Copy header, copy config.
            //
            SharedConfigHeader sharedHeader = sharedConfig.Header;
            TProxy configProxy = sharedConfig.Config;

            // Initialize header.
            //
            sharedHeader.ConfigId.Store(1);
            sharedHeader.CodegenTypeIndex = config.CodegenTypeIndex();

            // Copy the config to proxy.
            //
            CodegenTypeExtensions.Serialize(componentConfig.Config, sharedConfig.Config.Buffer);
        }
    }

    public partial struct SharedConfigMemoryRegion
    {
        /// <summary>
        /// Define property to Config Offsets array, as we allocate it dynamically.
        /// </summary>
        public UIntArray ConfigsOffsetArray => new UIntArray() { Buffer = buffer + (int)ConfigsArrayOffset };
    }
}
