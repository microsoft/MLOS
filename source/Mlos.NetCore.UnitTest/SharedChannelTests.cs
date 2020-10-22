// -----------------------------------------------------------------------
// <copyright file="SharedChannelTests.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Threading;
using System.Threading.Tasks;

using Mlos.Core;
using Mlos.UnitTest;
using Xunit;

using MlosProxyInternal = Proxy.Mlos.Core.Internal;
using TestSharedChannel = Mlos.Core.SharedChannel<Mlos.Core.InternalSharedChannelPolicy, Mlos.Core.SharedChannelSpinPolicy>;
using UnitTestProxy = Proxy.Mlos.UnitTest;

namespace Mlos.NetCore.UnitTest
{
    /// <summary>
    /// #TODO use InternalContext, configure shared memory view map.
    /// </summary>
    public sealed class SharedChannelTests : IDisposable
    {
        private const string GlobalMemoryMapName = "Mlos.NetCore.Global.UnitTest";
        private const string SharedChannelMemoryMapName = "Mlos.NetCore.SharedChannelTests.UnitTest";
        private const int SharedMemorySize = 65536;

        private readonly SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalChannelMemoryRegionView;
        private readonly SharedMemoryMapView sharedChannelMemoryMapView;
        private readonly TestSharedChannel sharedChannel;

        private bool isDisposed;

        public SharedChannelTests()
        {
            // Load the registry settings assemblies.
            //
            _ = SettingsAssemblyInitializer.GetGlobalDispatchTable();

            // Initialize shared channel.
            //
            globalChannelMemoryRegionView = SharedMemoryRegionView.CreateNew<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, SharedMemorySize);
            globalChannelMemoryRegionView.CleanupOnClose = true;
            sharedChannelMemoryMapView = SharedMemoryMapView.CreateNew(SharedChannelMemoryMapName, SharedMemorySize);
            sharedChannelMemoryMapView.CleanupOnClose = true;

            MlosProxyInternal.GlobalMemoryRegion globalMemoryRegion = globalChannelMemoryRegionView.MemoryRegion();

            sharedChannel = new TestSharedChannel(sharedChannelMemoryMapView, globalMemoryRegion.ControlChannelSynchronization);
        }

        public void Dispose()
        {
            this.Dispose(true);
            GC.SuppressFinalize(this);
        }

        private void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            globalChannelMemoryRegionView?.Dispose();
            sharedChannelMemoryMapView?.Dispose();
            isDisposed = true;
        }

        [Fact]
        public void SendReceiveMessages()
        {
            // Create a receiver task.
            //
            void ReceiverAction()
            {
                DispatchEntry[] globalDispatchTable = SettingsAssemblyInitializer.GetGlobalDispatchTable();

                bool result = true;
                while (result)
                {
                    result = sharedChannel.WaitAndDispatchFrame(globalDispatchTable);
                }
            }

            using Task receiverTask1 = Task.Factory.StartNew(ReceiverAction, CancellationToken.None, TaskCreationOptions.LongRunning, TaskScheduler.Current);
            using Task receiverTask2 = Task.Factory.StartNew(ReceiverAction, CancellationToken.None, TaskCreationOptions.LongRunning, TaskScheduler.Current);

            // Setup callbacks to verify the message.
            //
            UnitTestProxy.StringViewElements.Callback =
                msg =>
                {
                    Assert.Equal(1, msg.Item1.Id);
                    Assert.Equal("Test_Name101239871", msg.Item1.String.Value);
                    Assert.Equal(2, msg.Item2.Id);
                    Assert.Equal("Test_Abc", msg.Item2.String.Value);
                };

            UnitTestProxy.StringViewArray.Callback =
                msg =>
                {
                    Assert.Equal(1, msg.Id);
                    Assert.Equal("cba", msg.Strings[3].Value);
                };

            UnitTestProxy.WideStringMultiMessage.Callback =
                msg =>
                {
                    Assert.Equal(4, msg.StringMessages[0].Id);
                    Assert.Equal("Test_Name45659876", msg.StringMessages[0].Strings[3].Value);
                };

            int i = 0;
            while (i++ < 10000)
            {
                {
                    var msg = new StringViewElement();
                    msg.Id = 1;
                    msg.String.Value = "Test_Name101239871";

                    sharedChannel.SendMessage(ref msg);
                }

                {
                    var msg = new StringViewElements();
                    msg.Item1.Id = 1;
                    msg.Item1.String.Value = "Test_Name101239871";
                    msg.Item2.Id = 2;
                    msg.Item2.String.Value = "Test_Abc";

                    sharedChannel.SendMessage(ref msg);
                }

                {
                    var msg = new StringViewArray();
                    msg.Id = 1;
                    msg.Strings[0].Value = "12345";
                    msg.Strings[1].Value = "54321";
                    msg.Strings[2].Value = "abc";
                    msg.Strings[3].Value = "cba";
                    msg.Strings[4].Value = "sbs";

                    sharedChannel.SendMessage(ref msg);
                }

                {
                    // WideStringMultiMessage is a class (due to usage of fixed size arrays).
                    //
                    var msg = new WideStringMultiMessage();
                    msg.StringMessages[0].Id = 4;
                    msg.StringMessages[0].Strings[0].Value = "Test_Name9876";
                    msg.StringMessages[0].Strings[1].Value = "Test_Name19876";
                    msg.StringMessages[0].Strings[2].Value = null;
                    msg.StringMessages[0].Strings[3].Value = "Test_Name45659876";
                    msg.StringMessages[0].Strings[4].Value = "Test_Name901239876";

                    sharedChannel.SendMessage(ref msg);
                }
            }

            sharedChannel.Sync.TerminateChannel.Store(true);

            receiverTask1.Wait();
            receiverTask2.Wait();
        }
    }
}
