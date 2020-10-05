// -----------------------------------------------------------------------
// <copyright file="SharedConfigDictionaryLookup.cs" company="Microsoft Corporation">
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
    /// <summary>
    /// SharedConfigDictionary lookup implementation based on the given hash table probing policy.
    /// </summary>
    /// <typeparam name="TProbingPolicy">Probing policy.</typeparam>
    internal static class SharedConfigDictionaryLookup<TProbingPolicy>
        where TProbingPolicy : IProbingPolicy
    {
        /// <summary>
        /// Internal lookup. TProxy type is deduced by the caller.
        /// </summary>
        /// <typeparam name="TProxy">Codegen proxy type.</typeparam>
        /// <param name="sharedConfigDictionary"></param>
        /// <param name="codegenKey"></param>
        /// <param name="slotIndex"></param>
        /// <returns></returns>
        internal static SharedConfig<TProxy> Get<TProxy>(
            SharedConfigDictionary sharedConfigDictionary,
            ICodegenKey codegenKey,
            ref uint slotIndex)
            where TProxy : ICodegenProxy, new()
        {
            TProbingPolicy probingPolicy = default;

            uint probingCount = 0;
            slotIndex = 0;

            UIntArray configsArray = sharedConfigDictionary.ConfigsOffsetArray;

            uint elementCount = configsArray.Count;
            ProxyArray<uint> sharedConfigsOffsets = configsArray.Elements;

            SharedConfig<TProxy> sharedConfig = default;

            while (true)
            {
                slotIndex = probingPolicy.CalculateIndex(codegenKey, ref probingCount, elementCount);

                uint offsetToSharedConfig = sharedConfigsOffsets[(int)slotIndex];

                if (offsetToSharedConfig == 0)
                {
                    // Slot entry is empty.
                    //
                    sharedConfig.Buffer = IntPtr.Zero;
                    break;
                }

                // Compare the object keys.
                // Create a proxy to the shared config.
                //
                sharedConfig.Buffer = sharedConfigDictionary.Buffer - sharedConfigDictionary.Allocator.OffsetToAllocator + (int)offsetToSharedConfig;

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
        /// <typeparam name="TType">Codegen config type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy type.</typeparam>
        /// <param name="sharedConfigDictionary"></param>
        /// <param name="componentConfig"></param>
        internal static void Add<TType, TProxy>(
            SharedConfigDictionary sharedConfigDictionary,
            ComponentConfig<TType, TProxy> componentConfig)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;

            SharedConfig<TProxy> sharedConfig = Get<TProxy>(sharedConfigDictionary, componentConfig.Config, ref slotIndex);

            if (sharedConfig.Buffer != IntPtr.Zero)
            {
                throw new ArgumentException("Config already present", nameof(componentConfig));
            }

            TType config = componentConfig.Config;

            // Calculate size to allocate.
            //
            sharedConfig = sharedConfigDictionary.Allocator.Allocate<SharedConfig<TProxy>>();

            // Update hash map
            //
            ProxyArray<uint> sharedConfigOffsets = sharedConfigDictionary.ConfigsOffsetArray.Elements;

            // #TODO verify.
            sharedConfigOffsets[(int)slotIndex] = (uint)sharedConfig.Buffer.Offset(sharedConfigDictionary.Buffer - sharedConfigDictionary.Allocator.OffsetToAllocator);

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
}
