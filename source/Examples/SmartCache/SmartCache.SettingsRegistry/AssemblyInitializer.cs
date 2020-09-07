// -----------------------------------------------------------------------
// <copyright file="AssemblyInitializer.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

using Mlos.Core;
using Mlos.Model.Services;
using Mlos.Model.Services.Spaces;

using SmartCacheProxy = Proxy.SmartCache;

namespace SmartCache
{
    public static class AssemblyInitializer
    {
        private static IOptimizerProxy optimizerProxy;

        private static int isInCacheCount = 0;
        private static int totalRequestCount = 0;

        private static readonly JsonSerializerOptions JsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            WriteIndented = true,
            Converters =
            {
                new JsonStringEnumConverter(),
            },
        };

        static AssemblyInitializer()
        {
            // Setup message callbacks.
            //
            SmartCacheProxy.CacheRequestEventMessage.Callback = CacheRequestEventMessageHandler;
            SmartCacheProxy.RequestNewConfigurationMesage.Callback = RequestNewConfigurationMesageHandler;

            // Create smart cache parameter search space.
            //
            Hypergrid cacheSearchSpace = new Hypergrid(
                name: "smart_cache_config",
                dimension: new CategoricalDimension("cache_implementation", CacheEvictionPolicy.LeastRecentlyUsed, CacheEvictionPolicy.MostRecentlyUsed))
            .Join(
                subgrid: new Hypergrid(
                    name: "lru_cache_config",
                    dimension: new DiscreteDimension("cache_size", min: 1, max: 1 << 12)),
                onExternalDimension: new CategoricalDimension("cache_implementation", CacheEvictionPolicy.LeastRecentlyUsed))
            .Join(
                subgrid: new Hypergrid(
                    name: "mru_cache_config",
                    dimension: new DiscreteDimension("cache_size", min: 1, max: 1 << 12)),
                onExternalDimension: new CategoricalDimension("cache_implementation", CacheEvictionPolicy.MostRecentlyUsed));

            // Create optimization problem.
            //
            var optimizationProblem = new OptimizationProblem
            {
                ParameterSpace = cacheSearchSpace,
                ContextSpace = null,
                ObjectiveSpace = new Hypergrid(
                    name: "objectives",
                    dimensions: new ContinuousDimension(name: "HitRate", min: 0.0, max: 1.0)),
            };

            // Define optimization objective.
            //
            optimizationProblem.Objectives.Add(
                new OptimizationObjective
                {
                    Name = "HitRate",
                    Minimize = true,
                });

            IOptimizerFactory optimizerFactory = MlosContext.OptimizerFactory;

            optimizerProxy = optimizerFactory?.CreateRemoteOptimizer(optimizationProblem: optimizationProblem);
        }

        /// <summary>
        /// CacheRequestEventMessageHandler.
        /// </summary>
        /// <param name="msg"></param>
        private static void CacheRequestEventMessageHandler(SmartCacheProxy.CacheRequestEventMessage msg)
        {
            // Update hit rate
            //
            if (msg.IsInCache)
            {
                ++isInCacheCount;
            }

            ++totalRequestCount;
        }

        /// <summary>
        /// Request a new configuration from the optimizer.
        /// </summary>
        /// <param name="msg"></param>
        private static void RequestNewConfigurationMesageHandler(SmartCacheProxy.RequestNewConfigurationMesage msg)
        {
            SmartCacheProxy.SmartCacheConfig smartCacheConfig = MlosContext.SharedConfigManager.Lookup<SmartCacheProxy.SmartCacheConfig>().Config;

            if (optimizerProxy != null)
            {
                if (totalRequestCount != 0)
                {
                    double hitRate = (double)isInCacheCount / (double)totalRequestCount;

                    isInCacheCount = 0;
                    totalRequestCount = 0;

                    // Let's assemble an observation that consists of the config and the resulting performance.
                    //
                    var currentConfigDictionary = new Dictionary<string, object>();
                    currentConfigDictionary["cache_implementation"] = smartCacheConfig.EvictionPolicy;

                    _ = smartCacheConfig.EvictionPolicy switch
                    {
                        CacheEvictionPolicy.LeastRecentlyUsed => currentConfigDictionary["lru_cache_config.cache_size"] = smartCacheConfig.CacheSize,
                        CacheEvictionPolicy.MostRecentlyUsed => currentConfigDictionary["mru_cache_config.cache_size"] = smartCacheConfig.CacheSize,
                        _ => throw new NotImplementedException(),
                    };

                    string currentConfigJsonString = JsonSerializer.Serialize(currentConfigDictionary, JsonOptions);

                    // Register an observation.
                    //
                    optimizerProxy.Register(currentConfigJsonString, "HitRate", hitRate);
                }

                // Get new configuration.
                //
                string newConfigJsonString = optimizerProxy.Suggest();

                var newConfigDictionary = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(newConfigJsonString);

                // Update cache config.
                //
                smartCacheConfig.EvictionPolicy = Enum.Parse<CacheEvictionPolicy>(newConfigDictionary["cache_implementation"].GetString());

                smartCacheConfig.CacheSize = smartCacheConfig.EvictionPolicy switch
                {
                    CacheEvictionPolicy.LeastRecentlyUsed => (int)newConfigDictionary["lru_cache_config.cache_size"].GetDouble(),
                    CacheEvictionPolicy.MostRecentlyUsed => (int)newConfigDictionary["mru_cache_config.cache_size"].GetDouble(),
                    _ => throw new NotSupportedException(),
                };
            }

            // Send feedback message.
            //
            SharedConfigUpdatedFeedbackMessage feedbackMsg;
            MlosContext.FeedbackChannel.SendMessage(ref feedbackMsg);
        }
    }
}
