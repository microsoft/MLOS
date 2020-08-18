// -----------------------------------------------------------------------
// <copyright file="StreamingBenchmarks.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;
using System.Linq;

using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Jobs;
using BenchmarkDotNet.Running;

using Mlos.Streaming;

[SimpleJob(RuntimeMoniker.NetCoreApp31, baseline: true)]
[PlainExporter]
[HtmlExporter]
[MarkdownExporter]
[RPlotExporter]
[MemoryDiagnoser]
public class StreamingBenchmarks
{
    [Params(1000, 10000)]
    public int N;

    [GlobalSetup]
    public void Setup()
    {
    }

    private IEnumerable<int> intStream => Enumerable.Range(1, N);

    [Benchmark]
    public void LinqOnEnumerable()
    {
        _ = intStream.Min();
    }

    [Benchmark]
    public void LinqOnStream()
    {
        var collectionStream = new StreamableSource<int>();
        collectionStream.Min();
        collectionStream.Publish(intStream);
    }
}
