// -----------------------------------------------------------------------
// <copyright file="SharedMemoryRegionView.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.IO;
using System.Runtime.CompilerServices;

using MlosProxy = Proxy.Mlos.Core;
using MlosProxyInternal = Proxy.Mlos.Core.Internal;

namespace Mlos.Core
{
    public static class SharedMemoryRegionView
    {
        /// <summary>
        /// Creates a shared memory region view.
        /// </summary>
        /// <param name="sharedMemoryMapName"></param>
        /// <param name="sharedMemorySize"></param>
        /// <returns></returns>
        /// <typeparam name="T">Memory region type.</typeparam>
        public static SharedMemoryRegionView<T> CreateNew<T>(string sharedMemoryMapName, ulong sharedMemorySize)
            where T : ICodegenProxy, new()
        {
            var memoryRegionView = new SharedMemoryRegionView<T>(SharedMemoryMapView.CreateNew(sharedMemoryMapName, sharedMemorySize));

            MlosProxyInternal.MemoryRegionInitializer<T> memoryRegionInitializer = default;
            memoryRegionInitializer.Initalize(memoryRegionView);
            return memoryRegionView;
        }

        /// <summary>
        /// Creates or opens a shared memory region view.
        /// </summary>
        /// <param name="sharedMemoryMapName"></param>
        /// <param name="sharedMemorySize"></param>
        /// <returns></returns>
        /// <typeparam name="T">Memory region type.</typeparam>
        public static SharedMemoryRegionView<T> CreateOrOpen<T>(string sharedMemoryMapName, ulong sharedMemorySize)
            where T : ICodegenProxy, new()
        {
            try
            {
                return new SharedMemoryRegionView<T>(SharedMemoryMapView.OpenExisting(sharedMemoryMapName, sharedMemorySize));
            }
            catch (FileNotFoundException)
            {
                var memoryRegionView = new SharedMemoryRegionView<T>(SharedMemoryMapView.CreateNew(sharedMemoryMapName, sharedMemorySize));

                MlosProxyInternal.MemoryRegionInitializer<T> memoryRegionInitializer = default;
                memoryRegionInitializer.Initalize(memoryRegionView);
                return memoryRegionView;
            }
        }

        /// <summary>
        /// Opens an existing shared memory region view.
        /// </summary>
        /// <param name="sharedMemoryMapName"></param>
        /// <param name="sharedMemorySize"></param>
        /// <returns></returns>
        /// <typeparam name="T">Memory region type.</typeparam>
        public static SharedMemoryRegionView<T> OpenExisting<T>(string sharedMemoryMapName, ulong sharedMemorySize)
            where T : ICodegenProxy, new()
        {
            return new SharedMemoryRegionView<T>(SharedMemoryMapView.OpenExisting(sharedMemoryMapName, sharedMemorySize));
        }
    }

    /// <summary>
    /// Class represents shared memory map view for given type of memory region.
    /// </summary>
    /// <typeparam name="T">Memory region type.</typeparam>
    public sealed class SharedMemoryRegionView<T> : IDisposable
         where T : ICodegenProxy, new()
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="SharedMemoryRegionView{T}"/> class.
        /// </summary>
        /// <param name="sharedMemoryMap"></param>
        public SharedMemoryRegionView(SharedMemoryMapView sharedMemoryMap)
        {
            this.SharedMemoryMapView = sharedMemoryMap;

            var memoryRegion = new MlosProxyInternal.MemoryRegion
            {
                Buffer = sharedMemoryMap.Buffer,
                Signature = 0x67676767,
                MemoryRegionSize = sharedMemoryMap.MemSize,
                MemoryRegionCodeTypeIndex = default(T).CodegenTypeIndex(),
            };
        }

        /// <summary>
        /// Gets size of the shared memory map.
        /// </summary>
        public ulong MemSize => SharedMemoryMapView.MemSize;

        /// <summary>
        /// Returns an instance of MemoryRegionProxy.
        /// </summary>
        /// <returns></returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public T MemoryRegion()
        {
            return new T { Buffer = SharedMemoryMapView.Buffer };
        }

        #region IDisposable Support

        private void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            SharedMemoryMapView?.Dispose();
            SharedMemoryMapView = null;

            isDisposed = true;
        }

        /// <inheritdoc/>
        public void Dispose()
        {
            Dispose(true);
        }
        #endregion

        public SharedMemoryMapView SharedMemoryMapView { get; private set; }

        private bool isDisposed = false;

        /// <summary>
        /// Gets or sets a value indicating whether we should cleanup OS resources when closing the shared memory map view.
        /// </summary>
        public bool CleanupOnClose
        {
            get { return SharedMemoryMapView.CleanupOnClose; }
            set { SharedMemoryMapView.CleanupOnClose = value; }
        }
    }
}
