// -----------------------------------------------------------------------
// <copyright file="MainAgent.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;

using Mlos.Core;
using Proxy.Mlos.Core;

using MlosProxy = Proxy.Mlos.Core;
using MlosProxyInternal = Proxy.Mlos.Core.Internal;

namespace Mlos.Agent
{
    /// <summary>
    /// Mlos.Agent main class.
    /// </summary>
    public static class MainAgent
    {
        /// <remarks>
        /// Shared memory mapping name must start with "Host_" prefix, to be accessible from certain applications.
        /// TODO: Make these config regions configurable to support multiple processes.
        /// </remarks>
        private const string GlobalMemoryMapName = "Host_Mlos.GlobalMemory";
        private const string ControlChannelMemoryMapName = "Host_Mlos.ControlChannel";
        private const string FeedbackChannelMemoryMapName = "Host_Mlos.FeedbackChannel";
        private const string ControlChannelSemaphoreName = @"Global\ControlChannel_Event"; //// FIXME: Use non-backslashes for Linux environments.
        private const string FeedbackChannelSemaphoreName = @"Global\FeedbackChannel_Event";
        private const string SharedConfigMemoryMapName = "Host_Mlos.Config.SharedMemory";
        private const int SharedMemorySize = 65536;

        private static readonly SettingsAssemblyManager SettingsAssemblyManager = new SettingsAssemblyManager();

        private static readonly Dictionary<uint, SharedMemoryMapView> MemoryRegions = new Dictionary<uint, SharedMemoryMapView>();

        private static readonly SharedConfigManager SharedConfigManager = new SharedConfigManager();

        private static DispatchEntry[] globalDispatchTable = Array.Empty<DispatchEntry>();

        public static bool KeepRunning = true;

        #region Shared objects
        private static SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView;

        private static SharedMemoryMapView controlChannelMemoryMapView;
        private static SharedMemoryMapView feedbackChannelMemoryMapView;

        private static NamedEvent controlChannelNamedEvent;
        private static NamedEvent feedbackChannelNamedEvent;

        private static SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion> sharedConfigMemoryMapView;
        #endregion

        #region Mlos.Agent setup

        /// <summary>
        /// Initialize shared channel.
        /// </summary>
        public static void InitializeSharedChannel()
        {
            // Create or open the memory mapped files.
            //
            globalMemoryRegionView = SharedMemoryRegionView.CreateOrOpen<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, SharedMemorySize);
            controlChannelMemoryMapView = SharedMemoryMapView.CreateOrOpen(ControlChannelMemoryMapName, SharedMemorySize);
            feedbackChannelMemoryMapView = SharedMemoryMapView.CreateOrOpen(FeedbackChannelMemoryMapName, SharedMemorySize);
            sharedConfigMemoryMapView = SharedMemoryRegionView.CreateOrOpen<MlosProxyInternal.SharedConfigMemoryRegion>(SharedConfigMemoryMapName, SharedMemorySize);

            // Create channel synchronization primitives.
            //
            controlChannelNamedEvent = NamedEvent.CreateOrOpen(ControlChannelSemaphoreName);
            feedbackChannelNamedEvent = NamedEvent.CreateOrOpen(FeedbackChannelSemaphoreName);

            // Setup feedback channel.
            //
            MlosProxyInternal.GlobalMemoryRegion globalMemoryRegion = globalMemoryRegionView.MemoryRegion();

            // Enable channels.
            //
            globalMemoryRegion.ControlChannelSynchronization.TerminateChannel.Store(false);
            globalMemoryRegion.FeedbackChannelSynchronization.TerminateChannel.Store(false);

            var feedbackChannel = new SharedChannel<InterProcessSharedChannelPolicy, SharedChannelSpinPolicy>(
                buffer: feedbackChannelMemoryMapView.Buffer,
                size: (uint)feedbackChannelMemoryMapView.MemSize,
                sync: globalMemoryRegion.FeedbackChannelSynchronization);

            feedbackChannel.ChannelPolicy.NotificationEvent = feedbackChannelNamedEvent;

            // Set SharedConfig memory region.
            //
            SharedConfigManager.SetMemoryRegion(new MlosProxyInternal.SharedConfigMemoryRegion() { Buffer = sharedConfigMemoryMapView.MemoryRegion().Buffer });

            // Setup MlosContext.
            //
            MlosContext.FeedbackChannel = feedbackChannel;
            MlosContext.SharedConfigManager = SharedConfigManager;

            // Initialize callbacks.
            //
            MlosProxyInternal.RegisterAssemblyRequestMessage.Callback = RegisterAssemblyCallback;
            MlosProxyInternal.RegisterMemoryRegionRequestMessage.Callback = RegisterMemoryRegionMessageCallback;
            MlosProxyInternal.RegisterSharedConfigMemoryRegionRequestMessage.Callback = RegisterSharedConfigMemoryRegionRequestMessageCallback;
            MlosProxy.TerminateReaderThreadRequestMessage.Callback = TerminateReaderThreadRequestMessageCallback;

            // Register Mlos.Core assembly.
            //
            RegisterAssembly(typeof(MlosContext).Assembly, dispatchTableBaseIndex: 0);

            // Register assemblies from the shared config.
            // Assembly Mlos.NetCore does not have a config, as it is always registered first.
            //
            for (uint index = 1; index < globalMemoryRegion.RegisteredSettingsAssemblyCount.Load(); index++)
            {
                RegisterSettingsAssembly(assemblyIndex: index);
            }
        }

        /// <summary>
        /// Uninitialize shared channel.
        /// </summary>
        public static void UninitializeSharedChannel()
        {
            // Signal named event to close any waiter threads.
            //
            controlChannelNamedEvent.Signal();
            feedbackChannelNamedEvent.Signal();

            // Close shared memory.
            //
            controlChannelMemoryMapView.Dispose();
            feedbackChannelMemoryMapView.Dispose();
            sharedConfigMemoryMapView.Dispose();

            KeepRunning = false;
        }

        /// <summary>
        /// Register Component Assembly.
        /// </summary>
        /// <param name="assembly"></param>
        /// <param name="dispatchTableBaseIndex"></param>
        private static void RegisterAssembly(Assembly assembly, uint dispatchTableBaseIndex)
        {
            SettingsAssemblyManager.RegisterAssembly(assembly, dispatchTableBaseIndex);

            globalDispatchTable = SettingsAssemblyManager.GetGlobalDispatchTable();
        }

        /// <summary>
        /// Register next settings assembly.
        /// </summary>
        /// <param name="assemblyIndex"></param>
        public static void RegisterSettingsAssembly(uint assemblyIndex)
        {
            // Locate the settings assembly config.
            //
            var assemblyConfigKey = new Core.Internal.RegisteredSettingsAssemblyConfig.CodegenKey
            {
                AssemblyIndex = assemblyIndex,
            };

            SharedConfig<MlosProxyInternal.RegisteredSettingsAssemblyConfig> assemblySharedConfig = MlosContext.SharedConfigManager.Lookup(assemblyConfigKey);

            if (assemblySharedConfig.HasSharedConfig)
            {
                MlosProxyInternal.RegisteredSettingsAssemblyConfig assemblyConfig = assemblySharedConfig.Config;

                // Start looking for places to find the assembly.
                //
                List<string> assemblyDirs = new List<string>();

                // 1. Try to load assembly from the agent folder.
                //
                assemblyDirs.Add(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location));

                // 2. Try to load assembly from the full path listed in the config.
                // Note: This doesn't currently work for Linux.
                // See Also: Mlos.Core/MlosContext.cpp
                //
                if (assemblyConfig.ApplicationFilePath.Value != null)
                {
                    assemblyDirs.Add(Path.GetDirectoryName(assemblyConfig.ApplicationFilePath.Value));
                }

                // 3. The current working directory.
                //
                assemblyDirs.Add(".");

                // 4. The search path specified in an environment variable.
                // This is akin to an LD_LIBRARY_PATH but specifically for MLOS Settings Registry DLLs.
                //
                string settingsRegistryLibraryPath = System.Environment.GetEnvironmentVariable("MLOS_SETTINGS_REGISTRY_PATH");
                if (!string.IsNullOrEmpty(settingsRegistryLibraryPath))
                {
                    if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                    {
                        assemblyDirs.AddRange(settingsRegistryLibraryPath.Split(';'));
                    }
                    else if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                    {
                        assemblyDirs.AddRange(settingsRegistryLibraryPath.Split(':'));
                    }
                    else
                    {
                        throw new NotImplementedException(
                            string.Format("Unhandled OS: '{0}'", System.Runtime.InteropServices.RuntimeInformation.OSDescription ?? "Unknown"));
                    }
                }

                // Now, return the first full path to the assembly that we find.
                //
                string assemblyFilePath = null;
                string assemblyFileName = assemblyConfig.AssemblyFileName.Value;
                foreach (string assemblyDir in assemblyDirs)
                {
                    ////Console.WriteLine(string.Format("Checking for settings registry assembly {0} in {1}", assemblyFileName, assemblyDir));
                    string tmpAssemblyFilePath = Path.Combine(assemblyDir, assemblyFileName);
                    if (File.Exists(tmpAssemblyFilePath))
                    {
                        assemblyFilePath = tmpAssemblyFilePath;
                        Console.WriteLine(string.Format("Found settings registry assembly at {0}", assemblyFilePath));
                        break;
                    }
                }

                if (assemblyFilePath == null)
                {
                    throw new FileNotFoundException(string.Format("Failed to find settings registry assembly '{0}'", assemblyFileName));
                }

                Assembly assembly = Assembly.LoadFrom(assemblyFilePath);

                RegisterAssembly(assembly, dispatchTableBaseIndex: assemblyConfig.DispatchTableBaseIndex);
            }
        }

        /// <summary>
        /// Register next settings assembly.
        /// </summary>
        /// <param name="assembly"></param>
        public static void RegisterSettingsAssembly(Assembly assembly)
        {
            RegisterAssembly(assembly, SettingsAssemblyManager.CodegenTypeCount);
        }

        #endregion

        #region Messages callbacks

        /// <summary>
        /// Register Settings Assembly.
        /// </summary>
        /// <param name="registerAssemblyRequestMsg"></param>
        private static void RegisterAssemblyCallback(MlosProxyInternal.RegisterAssemblyRequestMessage registerAssemblyRequestMsg)
        {
            RegisterSettingsAssembly(registerAssemblyRequestMsg.AssemblyIndex);
        }

        /// <summary>
        /// Register memory region.
        /// </summary>
        /// <param name="msg"></param>
        private static void RegisterMemoryRegionMessageCallback(MlosProxyInternal.RegisterMemoryRegionRequestMessage msg)
        {
            if (!MemoryRegions.ContainsKey(msg.MemoryRegionId))
            {
                SharedMemoryMapView sharedMemoryMapView = SharedMemoryMapView.Open(
                    msg.Name.Value,
                    msg.MemoryRegionSize);

                MemoryRegions.Add(msg.MemoryRegionId, sharedMemoryMapView);
            }
        }

        /// <summary>
        /// Register shared config memory region.
        /// </summary>
        /// <param name="msg"></param>
        private static void RegisterSharedConfigMemoryRegionRequestMessageCallback(MlosProxyInternal.RegisterSharedConfigMemoryRegionRequestMessage msg)
        {
            // Store shared config memory region.
            //
            SharedMemoryMapView sharedConfigMemoryMapView = MemoryRegions[msg.MemoryRegionId];

            SharedConfigManager.SetMemoryRegion(new MlosProxyInternal.SharedConfigMemoryRegion() { Buffer = sharedConfigMemoryMapView.Buffer });
        }

        /// <summary>
        /// #TODO remove, this is not required.
        /// set the terminate channel in sync object and signal.
        /// </summary>
        /// <param name="msg"></param>
        private static void TerminateReaderThreadRequestMessageCallback(TerminateReaderThreadRequestMessage msg)
        {
            // Terminate the channel.
            //
            MlosProxyInternal.GlobalMemoryRegion globalMemoryRegion = globalMemoryRegionView.MemoryRegion();
            ChannelSynchronization controlChannelSync = globalMemoryRegion.ControlChannelSynchronization;
            controlChannelSync.TerminateChannel.Store(true);
        }

        #endregion

        /// <summary>
        /// Main.
        /// </summary>
        public static void RunAgent()
        {
            // Create the shared memory control channel.
            //
            var globalMemoryRegion = globalMemoryRegionView.MemoryRegion();
            var controlChannel = new SharedChannel<InterProcessSharedChannelPolicy, SharedChannelSpinPolicy>(
                buffer: controlChannelMemoryMapView.Buffer,
                size: (uint)controlChannelMemoryMapView.MemSize,
                sync: globalMemoryRegion.ControlChannelSynchronization);

            controlChannel.ChannelPolicy.NotificationEvent = controlChannelNamedEvent;

            // Create a thread that will monitor the reconfiguration request queue
            //
            bool result = true;
            while (result)
            {
                result = controlChannel.WaitAndDispatchFrame(globalDispatchTable);
            }
        }
    }
}
