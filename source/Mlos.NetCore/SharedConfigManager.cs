// -----------------------------------------------------------------------
// <copyright file="SharedConfigManager.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;

using Proxy.Mlos.Core.Internal;

using MlosProxyInternal = Proxy.Mlos.Core.Internal;

// Open hash table probing policy.
//
using ProbingPolicy = Mlos.Core.Collections.TLinearProbing<Mlos.Core.Collections.FNVHash<uint>>;

namespace Mlos.Core
{
    /// <summary>
    /// Shared config manager.
    /// </summary>
    /// <remarks>
    /// Config structures are stored in the shared memory.
    /// </remarks>
    public class SharedConfigManager : ISharedConfigAccessor, IDisposable
    {
        /// <summary>
        /// Lookup shared config by codegen key in given shared config dictionary.
        /// </summary>
        /// <typeparam name="TType">Codegen type.</typeparam>
        /// <typeparam name="TKey">Codegen key type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy.</typeparam>
        /// <param name="sharedConfigDictionary"></param>
        /// <param name="codegenKey"></param>
        /// <returns></returns>
        public static SharedConfig<TProxy> Lookup<TType, TKey, TProxy>(SharedConfigDictionary sharedConfigDictionary, ICodegenKey<TType, TKey, TProxy> codegenKey)
            where TType : ICodegenType, new()
            where TKey : ICodegenKey, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;
            return SharedConfigDictionaryLookup<ProbingPolicy>.Get<TProxy>(sharedConfigDictionary, codegenKey, ref slotIndex);
        }

        /// <summary>
        /// Registers a shared config memory region created by the target process.
        /// </summary>
        /// <param name="memoryRegionId"></param>
        /// <param name="sharedMemoryMapName"></param>
        /// <param name="memoryRegionSize"></param>
        public void RegisterSharedConfigMemoryRegion(uint memoryRegionId, string sharedMemoryMapName, ulong memoryRegionSize)
        {
            if (sharedConfigMemoryRegionView != null)
            {
                if (sharedConfigMemoryRegionView.MemoryRegion().MemoryHeader.MemoryRegionId == memoryRegionId)
                {
                    // Shared memory region has been already registered.
                    //
                    return;
                }
                else
                {
                    throw new NotImplementedException("Only a single shared config memory region is currently supported.");
                }
            }

            // Create a shared config memory region.
            //
            SharedMemoryMapView sharedConfigMemoryMapView = SharedMemoryMapView.OpenExisting(
                sharedMemoryMapName,
                memoryRegionSize);

            this.sharedConfigMemoryRegionView = new SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion>(sharedConfigMemoryMapView);
        }

        /// <inheritdoc/>
        public SharedConfig<TProxy> Lookup<TType, TKey, TProxy>(ICodegenKey<TType, TKey, TProxy> codegenKey)
            where TType : ICodegenType, new()
            where TKey : ICodegenKey, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;
            return SharedConfigDictionaryLookup<ProbingPolicy>.Get<TProxy>(SharedConfigDictionary, codegenKey, ref slotIndex);
        }

        /// <inheritdoc/>
        public SharedConfig<TProxy> Lookup<TType, TProxy>(ICodegenType<TType, TProxy> codegenType)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;
            return SharedConfigDictionaryLookup<ProbingPolicy>.Get<TProxy>(SharedConfigDictionary, codegenType, ref slotIndex);
        }

        /// <inheritdoc/>
        public SharedConfig<TProxy> Lookup<TProxy>()
            where TProxy : ICodegenProxy, new()
        {
            // #TODO make sure, ICodegenProxy does not have any fields to compare
            //
            uint slotIndex = 0;
            return SharedConfigDictionaryLookup<ProbingPolicy>.Get<TProxy>(SharedConfigDictionary, default(TProxy), ref slotIndex);
        }

        /// <summary>
        /// Insert element.
        /// </summary>
        /// <typeparam name="TType">Codegen configuration type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy.</typeparam>
        /// <param name="componentConfig"></param>
        public void UpdateConfig<TType, TProxy>(ComponentConfig<TType, TProxy> componentConfig)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;

            SharedConfig<TProxy> sharedConfig = SharedConfigDictionaryLookup<ProbingPolicy>.Get<TProxy>(SharedConfigDictionary, componentConfig.Config, ref slotIndex);

            if (sharedConfig.Buffer == IntPtr.Zero)
            {
                throw new KeyNotFoundException("Unable to locate config");
            }

            componentConfig.Config.Update(sharedConfig.Config);
        }

        /// <summary>
        /// Insert element.
        /// </summary>
        /// <typeparam name="TType">Codegen configuration type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy.</typeparam>
        /// <param name="componentConfig"></param>
        internal void Insert<TType, TProxy>(ComponentConfig<TType, TProxy> componentConfig)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            SharedConfigDictionaryLookup<ProbingPolicy>.Add<TType, TProxy>(SharedConfigDictionary, componentConfig);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            if (sharedConfigMemoryRegionView != null)
            {
                sharedConfigMemoryRegionView.CleanupOnClose |= CleanupOnClose;
                sharedConfigMemoryRegionView.Dispose();
                sharedConfigMemoryRegionView = null;
            }

            isDisposed = true;
        }

        public void Dispose()
        {
            Dispose(disposing: true);
            GC.SuppressFinalize(this);
        }

        public MlosProxyInternal.SharedConfigDictionary SharedConfigDictionary => SharedConfigMemoryRegion.SharedConfigDictionary;

        public MlosProxyInternal.SharedConfigMemoryRegion SharedConfigMemoryRegion => sharedConfigMemoryRegionView.MemoryRegion();

        /// <summary>
        /// Gets a value indicating whether if we should cleanup OS resources when closing the shared memory map view.
        /// </summary>
        public bool CleanupOnClose { get; internal set; }

        protected SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion> sharedConfigMemoryRegionView;

        protected bool isDisposed;
    }
}
