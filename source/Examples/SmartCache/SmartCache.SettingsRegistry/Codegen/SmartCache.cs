// -----------------------------------------------------------------------
// <copyright file="SmartCache.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;

namespace SmartCache
{
    public enum CacheEvictionPolicy
    {
        LeastRecentlyUsed,
        MostRecentlyUsed,
    }

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
    /// Ask optimizer for the new configuration.
    /// </summary>
    [CodegenMessage]
    internal partial struct RequestNewConfigurationMesage
    {
    }
}
