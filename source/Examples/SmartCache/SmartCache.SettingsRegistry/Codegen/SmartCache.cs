// -----------------------------------------------------------------------
// <copyright file="SmartCache.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------
//
// This file contains the data structures that represent both the component
// settings as well as the component specific messages it can send to and
// receive from the agent.
//
// Note: they are annotated with C# attributes that allow the MLOS code
// generation process to walk the structures using reflection.

using Mlos.SettingsSystem.Attributes;

namespace SmartCache
{
    public enum CacheEvictionPolicy
    {
        LeastRecentlyUsed,
        MostRecentlyUsed,
    }

    /// <summary>
    /// This is the collection of settings for the SmartCache component.
    /// To be made available in shared memory for both the agent and the
    /// component to use.
    /// </summary>
    [CodegenConfig]
    internal partial struct SmartCacheConfig
    {
        [ScalarSetting]
        internal long ConfigId;

        [ScalarSetting]
        internal CacheEvictionPolicy EvictionPolicy;

        [ScalarSetting]
        internal int CacheSize;
    }

    /// <summary>
    /// A telemetry message for the component to inform the agent of its progress.
    /// </summary>
    [CodegenMessage]
    internal partial struct CacheRequestEventMessage
    {
        [ScalarSetting]
        internal long ConfigId;

        // This is for the aggregator to build workload signature.
        //
        [ScalarSetting]
        internal ulong Key;

        [ScalarSetting]
        internal bool IsInCache;
    }

    /// <summary>
    /// A message to ask optimizer for the new configuration.
    /// </summary>
    /// <remarks>
    /// Note: This message contains no members to detail the request.
    /// It's very existence on the channel is signal enough of its intent.
    /// </remarks>
    [CodegenMessage]
    internal partial struct RequestNewConfigurationMessage
    {
    }
}
