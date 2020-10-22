// -----------------------------------------------------------------------
// <copyright file="SharedChannelBenchmarks.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;

using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Jobs;

using Mlos.Core;
using Mlos.UnitTest;

using MlosProxyInternal = Proxy.Mlos.Core.Internal;
using TestSharedChannel = Mlos.Core.SharedChannel<Mlos.Core.InternalSharedChannelPolicy, Mlos.Core.SharedChannelSpinPolicy>;
using UnitTestProxy = Proxy.Mlos.UnitTest;

/// <summary>
/// Base benchmark class.
/// </summary>
public class BaseSharedChannelBenchmark : IDisposable
{
    [DllImport("kernel32.dll")]
    private static extern IntPtr GetCurrentThread();

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern UIntPtr SetThreadAffinityMask(IntPtr handle, UIntPtr mask);

    private const string GlobalMemoryMapName = "Mlos.NetCore.Global.UnitTest";
    private const string SharedChannelMemoryMapName = "Mlos.NetCore.SharedChannelTests.UnitTest";
    private const int SharedMemorySize = 65536;

    private readonly SettingsAssemblyManager settingsAssemblyManager = new SettingsAssemblyManager();

    private readonly SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalChannelMemoryRegionView;
    private readonly SharedMemoryMapView sharedChannelMemoryMapView;
    private TestSharedChannel sharedChannel;

    private bool isDisposed;

    private StringViewArray stringViewArray;
    private WideStringMultiMessage wideStringMultiMessage;
    private Point pointMessage;

    public BaseSharedChannelBenchmark()
    {
        globalChannelMemoryRegionView = SharedMemoryRegionView.CreateNew<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, SharedMemorySize);
        sharedChannelMemoryMapView = SharedMemoryMapView.CreateNew(SharedChannelMemoryMapName, SharedMemorySize);

        MlosProxyInternal.GlobalMemoryRegion globalMemoryRegion = globalChannelMemoryRegionView.MemoryRegion();

        sharedChannel = new TestSharedChannel(sharedChannelMemoryMapView, globalMemoryRegion.ControlChannelSynchronization);

        settingsAssemblyManager.RegisterAssembly(typeof(MlosContext).Assembly);
        settingsAssemblyManager.RegisterAssembly(typeof(AssemblyInitializer).Assembly);

        // Preallocate class type messages to avoid heap allocations.
        //
        stringViewArray = new StringViewArray();
        stringViewArray.Id = 1;
        stringViewArray.Strings[0].Value = "12345";
        stringViewArray.Strings[1].Value = "54321";
        stringViewArray.Strings[2].Value = "abc";
        stringViewArray.Strings[3].Value = "cba";
        stringViewArray.Strings[4].Value = "sbs";

        wideStringMultiMessage = new WideStringMultiMessage();
        wideStringMultiMessage.StringMessages[0].Id = 4;
        wideStringMultiMessage.StringMessages[0].Strings[0].Value = "Test_Name9876";
        wideStringMultiMessage.StringMessages[0].Strings[1].Value = "Test_Name19876";
        wideStringMultiMessage.StringMessages[0].Strings[2].Value = "Test_Name1239876";
        wideStringMultiMessage.StringMessages[0].Strings[3].Value = "Test_Name45659876";
        wideStringMultiMessage.StringMessages[0].Strings[4].Value = "Test_Name901239876";

        pointMessage.X = 4;
        pointMessage.Y = 5;
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (isDisposed || !disposing)
        {
            return;
        }

        globalChannelMemoryRegionView?.Dispose();
        sharedChannelMemoryMapView?.Dispose();
        isDisposed = true;
    }

    public void Run(ulong messageCount, int readerCount)
    {
        // Create a receiver threads.
        //
        Thread[] receiverThreads = Enumerable.Range(1, readerCount).Select(
            (index) =>
            {
                Thread thread = new Thread(
                    (indexParam) =>
                {
                    int index = (int)indexParam;
                    UIntPtr affinityMask = new UIntPtr(1ul << index);
                    SetThreadAffinityMask(GetCurrentThread(), affinityMask);

                    DispatchEntry[] globalDispatchTable = settingsAssemblyManager.GetGlobalDispatchTable();

                    bool result = true;
                    while (result)
                    {
                        result = sharedChannel.WaitAndDispatchFrame(globalDispatchTable);
                    }
                });

                thread.Start(index);
                return thread;
            }).ToArray();

        // Setup callbacks to verify the message.
        //
        UnitTestProxy.StringViewArray.Callback =
            msg =>
            {
            };

        UnitTestProxy.WideStringMultiMessage.Callback =
            msg =>
            {
                if (string.Compare("Test_Name45659876", msg.StringMessages[0].Strings[3].Value, StringComparison.InvariantCulture) != 0)
                {
                    Environment.FailFast("Message failed");
                }
            };

        UnitTestProxy.Point.Callback =
            msg =>
            {
            };

        // Sender thread is on different logical core than receiver threads.
        //
        UIntPtr affinityMask = new UIntPtr(1ul);
        SetThreadAffinityMask(GetCurrentThread(), affinityMask);

        ulong index = 0;
        while (index++ < messageCount)
        {
            sharedChannel.SendMessage(ref stringViewArray);
            sharedChannel.SendMessage(ref wideStringMultiMessage);
            sharedChannel.SendMessage(ref pointMessage);
        }

        // Stop the test.
        //
        sharedChannel.Sync.TerminateChannel.Store(true);

        // Wait for all the receiver threads.
        //
        for (int i = 0; i < readerCount; i++)
        {
            receiverThreads[i].Join();
        }

        sharedChannel.Sync.TerminateChannel.Store(false);
    }
}

/// <summary>
/// Benchmark.
/// </summary>
/// <remarks>
/// The primary purpose of this benchmark is to verify that memory usage remains the same regardless of the number of messages sent.
/// </remarks>
[SimpleJob(RuntimeMoniker.NetCoreApp31)]
[PlainExporter]
[HtmlExporter]
[MarkdownExporter]
[RPlotExporter]
[MemoryDiagnoser]
public class SharedChannelMessagesCountBenchmarks : BaseSharedChannelBenchmark
{
    [Params(1000, 10000, 100000, 1000000)]
    public ulong MessageCount;

    [GlobalSetup]
    public void Setup()
    {
    }

    [GlobalCleanup]
    public void Cleanup()
    {
        Dispose();
    }

    [Benchmark]
    public void SendReceiveMessageCount()
    {
        Run(MessageCount, readerCount: 1);
    }
}

/// <summary>
/// Benchmark scale out number of readers.
/// </summary>
[SimpleJob(RuntimeMoniker.NetCoreApp31)]
[PlainExporter]
[HtmlExporter]
[MarkdownExporter]
[RPlotExporter]
[MemoryDiagnoser]
public class SharedChannelReaderScaleOutBenchmarks : BaseSharedChannelBenchmark
{
    [ParamsSource(nameof(ValuesForReaderCount))]
    public int ReaderCount;

    public IEnumerable<int> ValuesForReaderCount => new[] { 1, 2, 4, 8, 12, 16, 20, 24, 28, 32, 48 }.Where(r => r <= Environment.ProcessorCount);

    [GlobalSetup]
    public void Setup()
    {
    }

    [GlobalCleanup]
    public void Cleanup()
    {
        Dispose();
    }

    [Benchmark]
    public void SendReceiveReaderScaleOut()
    {
        // One sender thread.
        //
        Run(messageCount: 1000000, readerCount: Math.Min(ReaderCount, Environment.ProcessorCount - 1));
    }
}
