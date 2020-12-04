// -----------------------------------------------------------------------
// <copyright file="InterProcessMlosContext.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.IO;

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
        private const string ControlChannelMemoryMapName = "Host_Mlos.ControlChannel";
        private const string FeedbackChannelMemoryMapName = "Host_Mlos.FeedbackChannel";
        private const string ControlChannelEventName = @"Global\ControlChannel_Event"; //// FIXME: Use non-backslashes for Linux environments.
        private const string FeedbackChannelEventName = @"Global\FeedbackChannel_Event";
        private const string TargetProcessEventName = "Global\\Mlos_Global";

        private const int SharedMemorySize = 65536;

        /// <summary>
        /// Initializes a new instance of the <see cref="InterProcessMlosContext"/> class.
        /// </summary>
        /// <returns>InterProcessMlosContext instance.</returns>
        public static InterProcessMlosContext CreateOrOpen()
        {
            NamedEvent targetProcessNamedEvent = NamedEvent.CreateOrOpen(TargetProcessEventName);
            {
                bool shouldWaitForTargetProcess = false;

                try
                {
                    // Try open a global shared memory and check if the tager process is fully initialized.
                    //
                    using SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> targetProcessMemoryRegionView = SharedMemoryRegionView.OpenExisting<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, SharedMemorySize);

                    if (targetProcessMemoryRegionView.MemoryRegion().GlobalMemoryRegionIndex == 1)
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

            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView = SharedMemoryRegionView.OpenExisting<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, SharedMemorySize);
            SharedMemoryMapView controlChannelMemoryMapView = SharedMemoryMapView.OpenExisting(ControlChannelMemoryMapName, SharedMemorySize);
            SharedMemoryMapView feedbackChannelMemoryMapView = SharedMemoryMapView.OpenExisting(FeedbackChannelMemoryMapName, SharedMemorySize);

            // Create channel synchronization primitives.
            //
            NamedEvent controlChannelNamedEvent = NamedEvent.CreateOrOpen(ControlChannelEventName);
            NamedEvent feedbackChannelNamedEvent = NamedEvent.CreateOrOpen(FeedbackChannelEventName);

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
        internal InterProcessMlosContext(
            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView,
            SharedMemoryMapView controlChannelMemoryMapView,
            SharedMemoryMapView feedbackChannelMemoryMapView,
            NamedEvent controlChannelNamedEvent,
            NamedEvent feedbackChannelNamedEvent,
            NamedEvent targetProcessNamedEvent)
        {
            this.globalMemoryRegionView = globalMemoryRegionView;
            this.controlChannelMemoryMapView = controlChannelMemoryMapView;
            this.feedbackChannelMemoryMapView = feedbackChannelMemoryMapView;

            this.controlChannelNamedEvent = controlChannelNamedEvent;
            this.feedbackChannelNamedEvent = feedbackChannelNamedEvent;
            this.targetProcessNamedEvent = targetProcessNamedEvent;

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
        /// Notification event for the target process to avoid race conditions when creating
        /// shared memory regions. Target process signal this even after Mlos context is created.
        /// </summary>
        private readonly NamedEvent targetProcessNamedEvent;
    }
}
