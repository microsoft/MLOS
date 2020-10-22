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
    /// <summary>
    /// Initializer for this component Settings Registry assembly dll.
    /// </summary>
    /// <remarks>
    /// This class is instantiated by the C# Mlos.Agent (MainAgent.cs -
    /// RegisterSettingsAssembly) which calls
    /// <seealso cref="SettingsAssemblyManager" /> to invoke
    /// this one time initialization code for the settings and message handlers
    /// for this component's Settings Registry. This allows the Mlos.Agent (which
    /// is generic) to invoke the appropriate handlers for the component specific
    /// message handlers.
    /// The handlers can then communicate with an optimizer, adjust the
    /// component's shared memory config settings, and pass messages back to the
    /// component on the feedback channel.
    /// </remarks>
    public static class AssemblyInitializer
    {
        // Some variables for the tracking the telemetry received from the smart component.

        /// <summary>
        /// A running count of the number of hits in the cache.
        /// </summary>
        private static int isInCacheCount = 0;

        /// <summary>
        /// A running count of the total number of requests for the cache.
        /// </summary>
        private static int totalRequestCount = 0;

        /// <summary>
        /// A local reference to the connection to the optimizer service.
        /// </summary>
        private static readonly IOptimizerProxy OptimizerProxy;

        /// <remarks>
        /// Messages to the optimizer are handled using JSON, so this provides a
        /// standard serialization mechanism from C# Dictionary objects.
        /// </remarks>
        private static readonly JsonSerializerOptions JsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            WriteIndented = true,
            Converters =
            {
                new JsonStringEnumConverter(),
            },
        };

        /// <summary>
        /// Initializes static members of the <see cref="AssemblyInitializer"/> class.
        /// This is the entry point for setting up the message handlers for the
        /// messages code generated from the (partial) structs defined for this
        /// smart component in the CodeGen/SmartCache.cs.
        /// </summary>
        /// <remarks>
        /// See class comments for further details.
        /// </remarks>
        static AssemblyInitializer()
        {
            // Setup message callbacks.
            //
            // Note: these message properties are code generated from the
            // (partial) structs in CodeGen/SmartCache.cs
            //
            // See out/Mlos.CodeGen.out/SmartCache/*.cs for the C# code
            // generation output from those partial definitions.
            //
            SmartCacheProxy.CacheRequestEventMessage.Callback = CacheRequestEventMessageHandler;
            SmartCacheProxy.RequestNewConfigurationMessage.Callback = RequestNewConfigurationMessageHandler;

            // Create smart cache parameter search space.
            //
            // These hypergrids define the combination of valid ranges
            // of values for the different tunables.
            // Note that some of these are interdependent.
            //
            // TODO: Eventually this will also be code generated from additional
            // "domain range" attributes on the "ScalarSettings" defined for the
            // component (see also CodeGen/SmartCache.cs)
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
            // Here we declare to the optimizer what our desired output from the
            // component to optimize is.
            //
            // In this case we declare "hit rate", which will be calculated as a
            // percentage, is the thing we want the optimizer to improve.
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
                    // Tell the optimizer that we want to maximize hit rate.
                    //
                    Name = "HitRate",
                    Minimize = false,
                });

            // Get a local reference to the optimizer to reuse when processing messages later on.
            //
            // Note: we read this from a global variable that should have been
            // setup for the Mlos.Agent (e.g. in the Mlos.Agent.Server).
            //
            IOptimizerFactory optimizerFactory = MlosContext.Instance.OptimizerFactory;
            OptimizerProxy = optimizerFactory?.CreateRemoteOptimizer(optimizationProblem: optimizationProblem);
        }

        /// <summary>
        /// Handler to be called when receiving a CacheRequestEventMessage.
        /// </summary>
        /// <param name="msg">A reference to the message buffer.</param>
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
        /// Handler for a RequestNewConfigurationMessage from the smart componet.
        /// Receipt of such a message is used as a signal to request a new
        /// configuration from the optimizer and update the config in the shared
        /// memory region for the component.
        /// </summary>
        /// <param name="msg">A reference to the message buffer (unused).</param>
        private static void RequestNewConfigurationMessageHandler(SmartCacheProxy.RequestNewConfigurationMessage msg)
        {
            // Get a reference to the smart cache's config stored in shared memory.
            //
            SmartCacheProxy.SmartCacheConfig smartCacheConfig = MlosContext.Instance.SharedConfigManager.Lookup<SmartCacheProxy.SmartCacheConfig>().Config;

            // If we have a connection to the optimizer, then ask it for a new
            // configuration based on the stats from CacheRequestEvent telemetry
            // messages we've already received.
            //
            if (OptimizerProxy != null)
            {
                if (totalRequestCount != 0)
                {
                    double hitRate = (double)isInCacheCount / (double)totalRequestCount;

                    isInCacheCount = 0;
                    totalRequestCount = 0;

                    // Let's assemble an observation message that consists of
                    // the config and the resulting performance.
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

                    // Register the observation with the optimizer by sending it a grpc request.
                    //
                    Console.WriteLine("Register an observation");

                    OptimizerProxy.Register(currentConfigJsonString, "HitRate", hitRate);
                }

                // Now, ask the optimizer for a new configuration suggestion.
                //
                string newConfigJsonString = OptimizerProxy.Suggest();
                Console.WriteLine("Suggesting: " + newConfigJsonString);

                var newConfigDictionary = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(newConfigJsonString);

                // Update smart cache's config in shared memory with the
                // optimizer's new settings recommendation.
                //
                smartCacheConfig.EvictionPolicy = Enum.Parse<CacheEvictionPolicy>(newConfigDictionary["cache_implementation"].GetString());

                smartCacheConfig.CacheSize = smartCacheConfig.EvictionPolicy switch
                {
                    CacheEvictionPolicy.LeastRecentlyUsed => (int)newConfigDictionary["lru_cache_config.cache_size"].GetDouble(),
                    CacheEvictionPolicy.MostRecentlyUsed => (int)newConfigDictionary["mru_cache_config.cache_size"].GetDouble(),
                    _ => throw new NotSupportedException(),
                };
            }
            else
            {
                // No optimizer connection was found, so we will simply ignore
                // the request for a new configuration message for now and leave
                // the config as is.
            }

            // Send an (empty) "SharedConfigUpdated" message on the feedback
            // channel to let the SmartCache know that it can update it's
            // version of the config from shared memory.
            //
            SharedConfigUpdatedFeedbackMessage feedbackMsg;
            MlosContext.Instance.FeedbackChannel.SendMessage(ref feedbackMsg);
        }
    }
}
