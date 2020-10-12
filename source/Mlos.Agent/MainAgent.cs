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
using Proxy.Mlos.Core.Internal;

using MlosInternal = Mlos.Core.Internal;
using MlosProxy = Proxy.Mlos.Core;
using MlosProxyInternal = Proxy.Mlos.Core.Internal;

namespace Mlos.Agent
{
    /// <summary>
    /// Mlos.Agent main class.
    /// </summary>
    /// <remarks>
    /// Do not instantiate more than one instance of this class.
    /// </remarks>
    public class MainAgent : IDisposable
    {
        private readonly SettingsAssemblyManager settingsAssemblyManager = new SettingsAssemblyManager();

        private DispatchEntry[] globalDispatchTable = Array.Empty<DispatchEntry>();

        public bool KeepRunning = true;

        private bool isDisposed;

        #region Shared objects

        private MlosContext mlosContext;

        #endregion

        #region Mlos.Agent setup

        /// <summary>
        /// Initialize shared channel.
        /// </summary>
        /// <param name="mlosContext">Mlos context instance.</param>
        public void InitializeSharedChannel(MlosContext mlosContext)
        {
            // #TODO, implement experiment class.
            //
            MlosContext.Instance = mlosContext;
            this.mlosContext = mlosContext;

            // Initialize callbacks.
            //
            MlosProxyInternal.RegisterSettingsAssemblyRequestMessage.Callback = RegisterSettingsAssemblyCallback;
            MlosProxyInternal.RegisterSharedConfigMemoryRegionRequestMessage.Callback = RegisterSharedConfigMemoryRegionRequestMessageCallback;
            MlosProxy.TerminateReaderThreadRequestMessage.Callback = TerminateReaderThreadRequestMessageCallback;

            // Register Mlos.Core assembly.
            //
            RegisterAssembly(typeof(MlosContext).Assembly, dispatchTableBaseIndex: 0);

            // Register shared config memory regions.
            //
            for (uint index = 1; index < mlosContext.GlobalMemoryRegion.TotalMemoryRegionCount; index++)
            {
                // Skip first one as this is global memory region, and it does not require registration.
                //
                RegisterSharedConfigMemoryRegion(sharedMemoryRegionIndex: index + 1);
            }

            // Register assemblies from the shared config.
            // Assembly Mlos.NetCore does not have a config, as it is always registered first.
            //
            for (uint index = 1; index < mlosContext.GlobalMemoryRegion.RegisteredSettingsAssemblyCount.Load(); index++)
            {
                RegisterSettingsAssembly(assemblyIndex: index);
            }
        }

        /// <summary>
        /// Uninitialize shared channel.
        /// </summary>
        public void UninitializeSharedChannel()
        {
            KeepRunning = false;

            // Signal named event to close any waiter threads.
            //
            mlosContext.TerminateControlChannel();
            mlosContext.TerminateFeedbackChannel();
        }

        /// <summary>
        /// Register shared config memory region.
        /// </summary>
        /// <param name="sharedMemoryRegionIndex">Index of the shared memory region.</param>
        private void RegisterSharedConfigMemoryRegion(uint sharedMemoryRegionIndex)
        {
            MlosInternal.RegisteredMemoryRegionConfig.CodegenKey codegenKey = default;
            codegenKey.MemoryRegionIndex = sharedMemoryRegionIndex;

            // Locate shared memory region config.
            //
            SharedConfig<RegisteredMemoryRegionConfig> registeredMemoryRegionSharedConfig =
                SharedConfigManager.Lookup(mlosContext.GlobalMemoryRegion.SharedConfigDictionary, codegenKey);

            if (registeredMemoryRegionSharedConfig.HasSharedConfig)
            {
                // Config exists, register memory region with the shared config manager.
                //
                RegisteredMemoryRegionConfig registeredMemoryRegionConfig = registeredMemoryRegionSharedConfig.Config;

                mlosContext.SharedConfigManager.RegisterSharedConfigMemoryRegion(
                    memoryRegionId: registeredMemoryRegionConfig.MemoryRegionIndex,
                    sharedMemoryMapName: registeredMemoryRegionConfig.SharedMemoryMapName.Value,
                    memoryRegionSize: registeredMemoryRegionConfig.MemoryRegionSize);
            }
        }

        /// <summary>
        /// Register Component Assembly.
        /// </summary>
        /// <param name="assembly"></param>
        /// <param name="dispatchTableBaseIndex"></param>
        private void RegisterAssembly(Assembly assembly, uint dispatchTableBaseIndex)
        {
            settingsAssemblyManager.RegisterAssembly(assembly, dispatchTableBaseIndex);

            globalDispatchTable = settingsAssemblyManager.GetGlobalDispatchTable();
        }

        /// <summary>
        /// Register next settings assembly.
        /// </summary>
        /// <param name="assemblyIndex"></param>
        public void RegisterSettingsAssembly(uint assemblyIndex)
        {
            // Locate the settings assembly config.
            //
            var assemblyConfigKey = new Core.Internal.RegisteredSettingsAssemblyConfig.CodegenKey
            {
                AssemblyIndex = assemblyIndex,
            };

            SharedConfig<MlosProxyInternal.RegisteredSettingsAssemblyConfig> assemblySharedConfig =
                SharedConfigManager.Lookup(mlosContext.GlobalMemoryRegion.SharedConfigDictionary, assemblyConfigKey);

            if (assemblySharedConfig.HasSharedConfig)
            {
                MlosProxyInternal.RegisteredSettingsAssemblyConfig assemblyConfig = assemblySharedConfig.Config;

                // Start looking for places to find the assembly.
                //
                List<string> assemblyDirs = new List<string>();

                // 1. Try to load assembly from the agent folder.
                //
                assemblyDirs.Add(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location));

                // 2. The current working directory.
                //
                assemblyDirs.Add(".");

                // 3. The search path specified in an environment variable.
                // This is akin to an LD_LIBRARY_PATH but specifically for MLOS Settings Registry DLLs.
                //
                string settingsRegistryLibraryPath = System.Environment.GetEnvironmentVariable("MLOS_SETTINGS_REGISTRY_PATH");
                if (!string.IsNullOrEmpty(settingsRegistryLibraryPath))
                {
                    if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                    {
                        assemblyDirs.AddRange(settingsRegistryLibraryPath.Split(';'));
                    }
                    else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                    {
                        assemblyDirs.AddRange(settingsRegistryLibraryPath.Split(':'));
                    }
                    else
                    {
                        throw new NotImplementedException($"Unhandled OS: '{RuntimeInformation.OSDescription}'");
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
        public void RegisterSettingsAssembly(Assembly assembly)
        {
            RegisterAssembly(assembly, settingsAssemblyManager.CodegenTypeCount);
        }

        #endregion

        #region Messages callbacks

        /// <summary>
        /// Register Settings Assembly.
        /// </summary>
        /// <param name="msg"></param>
        private void RegisterSettingsAssemblyCallback(MlosProxyInternal.RegisterSettingsAssemblyRequestMessage msg)
        {
            RegisterSettingsAssembly(msg.AssemblyIndex);
        }

        /// <summary>
        /// Register shared config memory region.
        /// </summary>
        /// <param name="msg"></param>
        private void RegisterSharedConfigMemoryRegionRequestMessageCallback(MlosProxyInternal.RegisterSharedConfigMemoryRegionRequestMessage msg)
        {
            RegisterSharedConfigMemoryRegion(msg.MemoryRegionId);
        }

        /// <summary>
        /// #TODO remove, this is not required.
        /// </summary>
        /// <param name="msg"></param>
        private void TerminateReaderThreadRequestMessageCallback(MlosProxy.TerminateReaderThreadRequestMessage msg)
        {
            // Terminate the channel.
            //
            MlosProxy.ChannelSynchronization controlChannelSync = mlosContext.GlobalMemoryRegion.ControlChannelSynchronization;
            controlChannelSync.TerminateChannel.Store(true);
        }

        #endregion

        /// <summary>
        /// Main.
        /// </summary>
        public void RunAgent()
        {
            // Process the messages from the control channel.
            //
            mlosContext.ControlChannel.ProcessMessages(dispatchTable: ref globalDispatchTable);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            // Dispose MlosContext.
            //
            mlosContext?.Dispose();
            mlosContext = null;

            isDisposed = true;
        }

        public void Dispose()
        {
            Dispose(disposing: true);
            GC.SuppressFinalize(this);
        }
    }
}
