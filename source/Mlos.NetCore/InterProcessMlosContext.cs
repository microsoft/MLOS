// -----------------------------------------------------------------------
// <copyright file="InterProcessMlosContext.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using MlosProxy = Proxy.Mlos.Core;
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
        private const string ControlChannelSemaphoreName = @"Global\ControlChannel_Event"; //// FIXME: Use non-backslashes for Linux environments.
        private const string FeedbackChannelSemaphoreName = @"Global\FeedbackChannel_Event";

        private const string SharedConfigMemoryMapName = "Host_Mlos.Config.SharedMemory";

        private const int SharedMemorySize = 65536;

        /// <summary>
        /// Always create...
        /// </summary>
        /// <returns>InterProcessMlosContext instance.</returns>
        public static InterProcessMlosContext Create()
        {
            // Create or open the memory mapped files.
            //
            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView = SharedMemoryRegionView.Create<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, SharedMemorySize);
            SharedMemoryMapView controlChannelMemoryMapView = SharedMemoryMapView.Create(ControlChannelMemoryMapName, SharedMemorySize);
            SharedMemoryMapView feedbackChannelMemoryMapView = SharedMemoryMapView.Create(FeedbackChannelMemoryMapName, SharedMemorySize);
            SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion> sharedConfigMemoryMapView = SharedMemoryRegionView.Create<MlosProxyInternal.SharedConfigMemoryRegion>(SharedConfigMemoryMapName, SharedMemorySize);

            // Create channel synchronization primitives.
            //
            NamedEvent controlChannelNamedEvent = NamedEvent.CreateOrOpen(ControlChannelSemaphoreName);
            NamedEvent feedbackChannelNamedEvent = NamedEvent.CreateOrOpen(FeedbackChannelSemaphoreName);

            return new InterProcessMlosContext(
                globalMemoryRegionView,
                controlChannelMemoryMapView,
                feedbackChannelMemoryMapView,
                sharedConfigMemoryMapView,
                controlChannelNamedEvent,
                feedbackChannelNamedEvent);
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="InterProcessMlosContext"/> class.
        /// </summary>
        /// <returns>InterProcessMlosContext instance.</returns>
        public static InterProcessMlosContext CreateOrOpen()
        {
            // Create or open the memory mapped files.
            //
            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView = SharedMemoryRegionView.CreateOrOpen<MlosProxyInternal.GlobalMemoryRegion>(GlobalMemoryMapName, SharedMemorySize);
            SharedMemoryMapView controlChannelMemoryMapView = SharedMemoryMapView.CreateOrOpen(ControlChannelMemoryMapName, SharedMemorySize);
            SharedMemoryMapView feedbackChannelMemoryMapView = SharedMemoryMapView.CreateOrOpen(FeedbackChannelMemoryMapName, SharedMemorySize);
            SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion> sharedConfigMemoryMapView = SharedMemoryRegionView.CreateOrOpen<MlosProxyInternal.SharedConfigMemoryRegion>(SharedConfigMemoryMapName, SharedMemorySize);

            // Create channel synchronization primitives.
            //
            NamedEvent controlChannelNamedEvent = NamedEvent.CreateOrOpen(ControlChannelSemaphoreName);
            NamedEvent feedbackChannelNamedEvent = NamedEvent.CreateOrOpen(FeedbackChannelSemaphoreName);

            return new InterProcessMlosContext(
                globalMemoryRegionView,
                controlChannelMemoryMapView,
                feedbackChannelMemoryMapView,
                sharedConfigMemoryMapView,
                controlChannelNamedEvent,
                feedbackChannelNamedEvent);
        }

        internal InterProcessMlosContext(
            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView,
            SharedMemoryMapView controlChannelMemoryMapView,
            SharedMemoryMapView feedbackChannelMemoryMapView,
            SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion> sharedConfigMemoryMapView,
            NamedEvent controlChannelNamedEvent,
            NamedEvent feedbackChannelNamedEvent)
        {
            this.globalMemoryRegionView = globalMemoryRegionView;
            this.controlChannelMemoryMapView = controlChannelMemoryMapView;
            this.feedbackChannelMemoryMapView = feedbackChannelMemoryMapView;
            this.sharedConfigMemoryMapView = sharedConfigMemoryMapView;

            this.controlChannelNamedEvent = controlChannelNamedEvent;
            this.feedbackChannelNamedEvent = feedbackChannelNamedEvent;

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
                sharedConfigMemoryMapView.CleanupOnClose = true;
                controlChannelNamedEvent.CleanupOnClose = true;
                feedbackChannelNamedEvent.CleanupOnClose = true;
            }

            base.Dispose(disposing);
        }
    }
}
