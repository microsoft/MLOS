// -----------------------------------------------------------------------
// <copyright file="HashFunctionBenchmarks.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Linq;

using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Jobs;

using Mlos.Core.Collections;

[SimpleJob(RuntimeMoniker.NetCoreApp31)]
[PlainExporter]
[HtmlExporter]
[MarkdownExporter]
[MemoryDiagnoser]
public class HashFunctionBenchmarks
{
    public static string SequenceString;

    [Params(20000000)]
    public int N;

    [GlobalSetup]
    public void Setup()
    {
        SequenceString = string.Join('-', Enumerable.Range(1, 1024 * 1024));
    }

    [Benchmark]
    public ulong NVMULongHashInt()
    {
        ulong sum = 0;

        for (int i = 0; i < N; i++)
        {
            sum += default(FNVHash<ulong>).GetHashValue(i);
        }

        return sum;
    }

    [Benchmark(Baseline =true)]
    public ulong NVMULongHashSpecializedInt()
    {
        ulong sum = 0;

        for (int i = 0; i < N; i++)
        {
            sum += FNVHash<ulong>.GetHashValueULong(i);
        }

        return sum;
    }

    [Benchmark]
    public ulong NVMIntHashGenericInt()
    {
        uint sum = 0;

        for (int i = 0; i < N; i++)
        {
            sum += default(FNVHash<uint>).GetHashValue(i);
        }

        return sum;
    }

    [Benchmark]
    public ulong NVMStringHash()
    {
        ulong sum = 0;

        sum += default(FNVHash<ulong>).GetHashValue(SequenceString);

        return sum;
    }
}
