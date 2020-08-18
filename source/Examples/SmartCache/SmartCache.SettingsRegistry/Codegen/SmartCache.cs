// -----------------------------------------------------------------------
// <copyright file="SmartCache.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace SmartCache
{
    /// <summary>
    /// TODO: learn to use and extend this.
    /// </summary>
    [CodegenConfig]
    internal partial struct SmartCacheConfig
    {
        [ScalarSetting]
        internal long ConfigId;

        [ScalarSetting]
        internal ulong TelemetryBitMask;

        [ScalarSetting]
        internal int CacheSize;
    }

    [Flags]
    public enum TelemetryMasks : ulong
    {
        KeyAccessEvent = 1,
        ThroughputMetrics = 2,
    }

    [CodegenMessage]
    internal partial struct CacheRequestEventMessage
    {
        // This is to uniquely identify which cache is being pounded.
        //
        internal ulong CacheAddress;

        // This is for the aggregator to build workload signature.
        //
        internal ulong KeyValue;
    }
}