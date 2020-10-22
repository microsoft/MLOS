// -----------------------------------------------------------------------
// <copyright file="SharedMemoryMapViewTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.IO;
using System.Threading.Tasks;

using Mlos.Core;
using Mlos.UnitTest;
using Xunit;

using MlosProxyInternal = Proxy.Mlos.Core.Internal;
using TestSharedChannel = Mlos.Core.SharedChannel<Mlos.Core.InternalSharedChannelPolicy, Mlos.Core.SharedChannelSpinPolicy>;
using UnitTestProxy = Proxy.Mlos.UnitTest;

namespace Mlos.NetCore.UnitTest
{
    public sealed class SharedMemoryMapViewTests
    {
        private const string SharedMemoryMapName = "Mlos.NetCore.SharedMapTest.UnitTest";
        private const int SharedMemorySize = 4096;

        /// <summary>
        /// Verifies that on Linux, shared memory is unlinked on dispose.
        /// </summary>
        [Fact]
        public void VerifySharedMemoryMapUnlink()
        {
            // Create a new shared memory maps.
            //
            var newsSharedChannelMemoryMap = SharedMemoryMapView.CreateNew(SharedMemoryMapName, SharedMemorySize);
            newsSharedChannelMemoryMap.CleanupOnClose = true;
            newsSharedChannelMemoryMap.Dispose();

            try
            {
                // Verify we can open already created shared memory.
                //
                using var openedSharedChannelMemoryMap = SharedMemoryMapView.OpenExisting(SharedMemoryMapName, SharedMemorySize);
                newsSharedChannelMemoryMap.CleanupOnClose = true;

                Assert.False(true, "Shared memory map should be deleted");
            }
            catch (FileNotFoundException)
            {
                // We are expecting failure.
                //
            }
        }
    }
}
