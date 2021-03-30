// -----------------------------------------------------------------------
// <copyright file="InterProcessMlosContext.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.IO;

using Proxy.Mlos.Core.Internal;

using MlosInternal = Mlos.Core.Internal;
using MlosProxyInternal = Proxy.Mlos.Core.Internal;

namespace Mlos.Core
{
    /// <summary>
    /// Inter-process MlosContexts.
    /// </summary>
    public class InterProcessMlosContext : MlosContext
    {
        /// <remarks>
        /// Shared memory mapping name must start with "Host_" prefix, to be accessible from certain applications.
        /// TODO: Make these config regions configurable to support multiple processes.
        /// </remarks>
        private const string GlobalMemoryMapName = "Host_Mlos.GlobalMemory";
        private const string TargetProcessEventName = "Global\\Mlos_Global";

        /// <summary>
        /// Initializes a new instance of the <see cref="InterProcessMlosContext"/> class.
        /// </summary>
        /// <returns>InterProcessMlosContext instance.</returns>
        public static InterProcessMlosContext Create()
        {
            var targetProcessNamedEvent = NamedEvent.CreateOrOpen(TargetProcessEventName);
            {
                bool shouldWaitForTargetProcess = false;

                try
                {
                    // Try open a global shared memory and check if the target process is fully initialized.
                    //
                    using var targetProcessMemoryRegionView = SharedMemoryRegionView.OpenExisting<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, MlosInternal.GlobalMemoryRegion.GlobalSharedMemorySize);

                    // If RegisteredSettingsAssemblyCount is 0, the context is not created.
                    //
                    if (targetProcessMemoryRegionView.MemoryRegion().RegisteredSettingsAssemblyCount.Load() == 0)
                    {
                        shouldWaitForTargetProcess = true;
                    }
                }
                catch (FileNotFoundException)
                {
                    // If the target process is not running.
                    //
                    shouldWaitForTargetProcess = true;
                }

                if (shouldWaitForTargetProcess)
                {
                    // If the target process is not fully initialized, wait for the signal.
                    //
                    targetProcessNamedEvent.Wait();
                    targetProcessNamedEvent.Signal();
                }
            }

            // Open global memory region.
            //
            var globalMemoryRegionView = SharedMemoryRegionView.OpenExisting<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, MlosInternal.GlobalMemoryRegion.GlobalSharedMemorySize);
            GlobalMemoryRegion globalMemoryRegion = globalMemoryRegionView.MemoryRegion();

            // Open existing shared channels memory maps.
            //
            globalMemoryRegion.TryOpenExisting(
                new MlosInternal.MemoryRegionId { Type = MlosInternal.MemoryRegionType.ControlChannel, Index = 0, },
                out SharedMemoryMapView controlChannelMemoryMapView);

            globalMemoryRegion.TryOpenExisting(
                new MlosInternal.MemoryRegionId { Type = MlosInternal.MemoryRegionType.FeedbackChannel, Index = 0, },
                out SharedMemoryMapView feedbackChannelMemoryMapView);

            // Open existing channel synchronization primitives.
            //
            globalMemoryRegion.TryOpenExisting(
                new MlosInternal.MemoryRegionId { Type = MlosInternal.MemoryRegionType.ControlChannel,  Index = 0, },
                out NamedEvent controlChannelNamedEvent);

            globalMemoryRegion.TryOpenExisting(
                new MlosInternal.MemoryRegionId { Type = MlosInternal.MemoryRegionType.FeedbackChannel,  Index = 0, },
                out NamedEvent feedbackChannelNamedEvent);

            return new InterProcessMlosContext(
                globalMemoryRegionView,
                controlChannelMemoryMapView,
                feedbackChannelMemoryMapView,
                controlChannelNamedEvent,
                feedbackChannelNamedEvent,
                targetProcessNamedEvent);
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="InterProcessMlosContext"/> class.
        /// </summary>
        /// <param name="globalMemoryRegionView"></param>
        /// <param name="controlChannelMemoryMapView"></param>
        /// <param name="feedbackChannelMemoryMapView"></param>
        /// <param name="controlChannelNamedEvent"></param>
        /// <param name="feedbackChannelNamedEvent"></param>
        /// <param name="targetProcessNamedEvent"></param>
        private InterProcessMlosContext(
            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView,
            SharedMemoryMapView controlChannelMemoryMapView,
            SharedMemoryMapView feedbackChannelMemoryMapView,
            NamedEvent controlChannelNamedEvent,
            NamedEvent feedbackChannelNamedEvent,
            NamedEvent targetProcessNamedEvent)
        {
            this.globalMemoryRegionView = globalMemoryRegionView ?? throw new ArgumentNullException(nameof(globalMemoryRegionView));
            this.controlChannelMemoryMapView = controlChannelMemoryMapView ?? throw new ArgumentNullException(nameof(controlChannelMemoryMapView));
            this.feedbackChannelMemoryMapView = feedbackChannelMemoryMapView ?? throw new ArgumentNullException(nameof(feedbackChannelMemoryMapView));

            this.controlChannelNamedEvent = controlChannelNamedEvent ?? throw new ArgumentNullException(nameof(controlChannelNamedEvent));
            this.feedbackChannelNamedEvent = feedbackChannelNamedEvent ?? throw new ArgumentNullException(nameof(feedbackChannelNamedEvent));
            this.targetProcessNamedEvent = targetProcessNamedEvent ?? throw new ArgumentNullException(nameof(targetProcessNamedEvent));

            // Create the shared config manager.
            //
            SharedConfigManager = new SharedConfigManager();

            MlosProxyInternal.GlobalMemoryRegion globalMemoryRegion = globalMemoryRegionView.MemoryRegion();

            // Increase the usage counter. When closing global shared memory, we will decrease the counter.
            // If there is no process using the shared memory, we will clean the OS resources. On Windows OS,
            // this is no-op; on Linux, we unlink created files.
            //
            globalMemoryRegion.AttachedProcessesCount.FetchAdd(1);

            // Create the control channel instance.
            //
            ControlChannel = new SharedChannel<InterProcessSharedChannelPolicy, SharedChannelSpinPolicy>(
                buffer: controlChannelMemoryMapView.Buffer,
                size: (uint)controlChannelMemoryMapView.MemSize,
                sync: globalMemoryRegion.ControlChannelSynchronization)
            {
                ChannelPolicy = { NotificationEvent = controlChannelNamedEvent },
            };

            // Create the feedback channel instance.
            //
            FeedbackChannel = new SharedChannel<InterProcessSharedChannelPolicy, SharedChannelSpinPolicy>(
                buffer: feedbackChannelMemoryMapView.Buffer,
                size: (uint)feedbackChannelMemoryMapView.MemSize,
                sync: globalMemoryRegion.FeedbackChannelSynchronization)
            {
                ChannelPolicy = { NotificationEvent = feedbackChannelNamedEvent },
            };

            // Register config region if available.
            //
            if (globalMemoryRegion.TryOpenExisting(
                new MlosInternal.MemoryRegionId { Type = MlosInternal.MemoryRegionType.SharedConfig, Index = 0, },
                out SharedMemoryMapView sharedConfigMemoryMap))
            {
                var sharedMemoryRegionView = new SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion>(sharedConfigMemoryMap);

                SharedConfigManager.RegisterSharedConfigMemoryRegion(sharedMemoryRegionView);
            }
            else
            {
                sharedConfigMemoryMap?.Dispose();
            }
        }

        /// <inheritdoc/>
        protected override void Dispose(bool disposing)
        {
            if (isDisposed || !disposing)
            {
                return;
            }

            uint usageCount = GlobalMemoryRegion.AttachedProcessesCount.FetchSub(1);

            // The last one out shut off the lights.
            //
            if (usageCount == 0)
            {
                globalMemoryRegionView.CleanupOnClose = true;
                controlChannelMemoryMapView.CleanupOnClose = true;
                feedbackChannelMemoryMapView.CleanupOnClose = true;
                controlChannelNamedEvent.CleanupOnClose = true;
                feedbackChannelNamedEvent.CleanupOnClose = true;
                targetProcessNamedEvent.CleanupOnClose = true;

                // Close all the shared config memory regions.
                //
                SharedConfigManager.CleanupOnClose = true;
            }

            base.Dispose(disposing: true);
        }

        /// <summary>
        /// The target process uses this notification event to avoid race conditions when creating shared memory regions.
        /// The process signals the event after creating the context.
        /// </summary>
        private readonly NamedEvent targetProcessNamedEvent;
    }
}
