// -----------------------------------------------------------------------
// <copyright file="SharedConfigManagerTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.Core;
using Mlos.UnitTest;

using Xunit;

using MlosProxyInternal = Proxy.Mlos.Core.Internal;
using UnitTestProxy = Proxy.Mlos.UnitTest;

//
// Alternating signs if the number of buckets is a prime number {\displaystyle p}p congruent to 3 modulo 4 (e.g. 3, 7, 11, 19, 23, 31, etc.), then the first p offsets will be unique.
// https://en.wikipedia.org/wiki/Quadratic_probing
//
// Given that M is a prime number, and M = 3 (mod 4).
// 1019 % 4 == 3
//
namespace Mlos.NetCore.UnitTest
{
    public class SharedConfigManagerTests
    {
        private const int SharedMemorySize = 65536 * 4;
        private const string SharedMemoryMapName = "Mlos.NetCore.SharedMemory.UnitTest";

        public SharedConfigManagerTests()
        {
            // Load the registry settings assemblies.
            //
            _ = SettingsAssemblyInitializer.GetGlobalDispatchTable();
        }

        [Fact]
        public void Insert()
        {
            // Create a shared memory map.
            //
            using var sharedMemoryRegionView = SharedMemoryRegionView.CreateNew<MlosProxyInternal.SharedConfigMemoryRegion>(SharedMemoryMapName, SharedMemorySize);
            sharedMemoryRegionView.CleanupOnClose = true;

            // Create a shared config manager, and register created test shared memory map.
            //
            using var sharedConfigManager = new SharedConfigManager();
            sharedConfigManager.RegisterSharedConfigMemoryRegion(memoryRegionId: 1, sharedMemoryMapName: SharedMemoryMapName, memoryRegionSize: SharedMemorySize);
            sharedConfigManager.CleanupOnClose = true;

            for (int i = 0; i < 500; i++)
            {
                {
                    TestComponentConfig config = default;
                    config.ComponentType = (uint)(i + 1);
                    config.Category = 2;
                    config.Delay = 5;

                    var componentConfig = ComponentConfig.Create(config);

                    sharedConfigManager.Insert(componentConfig);
                }

                {
                    var componentConfig = new ComponentConfig<TestComponentConfig, UnitTestProxy.TestComponentConfig>();

                    componentConfig.Config.ComponentType = (uint)(i + 1);
                    componentConfig.Config.Category = 2;

                    sharedConfigManager.UpdateConfig(componentConfig);
                    Assert.Equal<double>(5, componentConfig.Config.Delay);
                }

                {
                    var componentConfig = new ComponentConfig<TestComponentStatistics, UnitTestProxy.TestComponentStatistics>();
                    componentConfig.Config.Id = i;
                    componentConfig.Config.RefCount.Value = 5;
                    componentConfig.Config.Counters[0].Value = 2;

                    sharedConfigManager.Insert(componentConfig);
                }
            }

            for (int i = 0; i < 500; i++)
            {
                {
                    var componentConfig = new ComponentConfig<TestComponentConfig, UnitTestProxy.TestComponentConfig>();

                    componentConfig.Config.ComponentType = (uint)(i + 1);
                    componentConfig.Config.Category = 2;

                    sharedConfigManager.UpdateConfig(componentConfig);
                    Assert.Equal<double>(5, componentConfig.Config.Delay);
                }

                {
                    var componentConfig = new ComponentConfig<TestComponentStatistics, UnitTestProxy.TestComponentStatistics>();
                    componentConfig.Config.Id = i;

                    sharedConfigManager.UpdateConfig(componentConfig);

                    Assert.Equal<ulong>(5, componentConfig.Config.RefCount.Value);
                    Assert.Equal<ulong>(2, componentConfig.Config.Counters[0].Value);
                }

                {
                    var componentStatistics = new TestComponentStatistics() { Id = i };
                    SharedConfig<UnitTestProxy.TestComponentStatistics> sharedConfig = sharedConfigManager.Lookup(componentStatistics);
                }

                {
                    TestComponentStatistics.CodegenKey codegenKey = default;
                    codegenKey.Id = i;

                    SharedConfig<UnitTestProxy.TestComponentStatistics> sharedConfig = sharedConfigManager.Lookup(codegenKey);

                    Assert.Equal<ulong>(5, sharedConfig.Config.RefCount.Load());
                    Assert.Equal<ulong>(2, sharedConfig.Config.Counters[0].Load());
                }
            }
        }
    }
}
