// -----------------------------------------------------------------------
// <copyright file="AnonymousMemoryMlosContext.Linux.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.Core.Internal;

using MlosProxyInternal = Proxy.Mlos.Core.Internal;

namespace Mlos.Core.Linux
{
    /// <summary>
    ///  Implementation of an inter-process MlosContext based on anonymous shared memory.
    ///  Shared memory file descriptors are exchanged using Unix domain socket.
    /// </summary>
    public class AnonymousMemoryMlosContext : MlosContext
    {
        // File exchange Unix domain socket name.
        //
        private const string FdUnitDomainSocketName = "/tmp/mlos.sock";

        // Synchronization semaphore names.
        //
        private const string FdExchangeSemaphoreName = "mlos_fd_exchange";
        private const string ControlChannelSemaphoreName = "mlos_control_channel_event";
        private const string FeedbackChannelSemaphoreName = "mlos_feedback_channel_event";

        /// <summary>
        /// Creates InterProcessMlosContext.
        /// </summary>
        /// <returns></returns>
        public static AnonymousMemoryMlosContext Create()
        {
            var fdExchangeServer = new FileDescriptorExchangeServer(FdUnitDomainSocketName, FdExchangeSemaphoreName);
            fdExchangeServer.HandleRequests();

            MemoryRegionId memoryRegionId = new MemoryRegionId { Type = MemoryRegionType.Global };
            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView =
                SharedMemoryRegionView.OpenAnonymousFromFileDescriptor<MlosProxyInternal.GlobalMemoryRegion>(
                    fdExchangeServer.GetSharedMemoryFd(memoryRegionId),
                    fdExchangeServer.GetSharedMemorySize(memoryRegionId));

            memoryRegionId = new MemoryRegionId { Type = MemoryRegionType.ControlChannel };
            SharedMemoryMapView controlChannelMemoryMapView = SharedMemoryMapView.OpenAnonymousFromFileDescriptor(
                fdExchangeServer.GetSharedMemoryFd(memoryRegionId),
                fdExchangeServer.GetSharedMemorySize(memoryRegionId));

            memoryRegionId = new MemoryRegionId { Type = MemoryRegionType.FeedbackChannel };
            SharedMemoryMapView feedbackChannelMemoryMapView = SharedMemoryMapView.OpenAnonymousFromFileDescriptor(
                fdExchangeServer.GetSharedMemoryFd(memoryRegionId),
                fdExchangeServer.GetSharedMemorySize(memoryRegionId));

            memoryRegionId = new MemoryRegionId { Type = MemoryRegionType.SharedConfig };
            SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion> sharedConfigMemoryRegionView =
                SharedMemoryRegionView.OpenAnonymousFromFileDescriptor<MlosProxyInternal.SharedConfigMemoryRegion>(
                fdExchangeServer.GetSharedMemoryFd(memoryRegionId),
                fdExchangeServer.GetSharedMemorySize(memoryRegionId));

            // Create channel synchronization primitives.
            //
            NamedEvent controlChannelNamedEvent = NamedEvent.CreateOrOpen(ControlChannelSemaphoreName);
            NamedEvent feedbackChannelNamedEvent = NamedEvent.CreateOrOpen(FeedbackChannelSemaphoreName);

            return new AnonymousMemoryMlosContext(
                globalMemoryRegionView,
                controlChannelMemoryMapView,
                feedbackChannelMemoryMapView,
                sharedConfigMemoryRegionView,
                controlChannelNamedEvent,
                feedbackChannelNamedEvent,
                fdExchangeServer);
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="AnonymousMemoryMlosContext"/> class.
        /// </summary>
        /// <param name="globalMemoryRegionView"></param>
        /// <param name="controlChannelMemoryMapView"></param>
        /// <param name="feedbackChannelMemoryMapView"></param>
        /// <param name="sharedConfigMemoryRegionView"></param>
        /// <param name="controlChannelNamedEvent"></param>
        /// <param name="feedbackChannelNamedEvent"></param>
        /// <param name="fileDescriptorExchangeServer"></param>
        private AnonymousMemoryMlosContext(
            SharedMemoryRegionView<MlosProxyInternal.GlobalMemoryRegion> globalMemoryRegionView,
            SharedMemoryMapView controlChannelMemoryMapView,
            SharedMemoryMapView feedbackChannelMemoryMapView,
            SharedMemoryRegionView<MlosProxyInternal.SharedConfigMemoryRegion> sharedConfigMemoryRegionView,
            NamedEvent controlChannelNamedEvent,
            NamedEvent feedbackChannelNamedEvent,
            FileDescriptorExchangeServer fileDescriptorExchangeServer)
        {
            this.globalMemoryRegionView = globalMemoryRegionView;
            this.controlChannelMemoryMapView = controlChannelMemoryMapView;
            this.feedbackChannelMemoryMapView = feedbackChannelMemoryMapView;

            this.controlChannelNamedEvent = controlChannelNamedEvent;
            this.feedbackChannelNamedEvent = feedbackChannelNamedEvent;

            this.fileDescriptorExchangeServer = fileDescriptorExchangeServer;

            // Create the shared config manager.
            //
            SharedConfigManager = new SharedConfigManager();

            // Register shared config memory region.
            //
            SharedConfigManager.RegisterSharedConfigMemoryRegion(sharedConfigMemoryRegionView);

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

            fileDescriptorExchangeServer?.Dispose();
            fileDescriptorExchangeServer = null;

            uint usageCount = GlobalMemoryRegion.AttachedProcessesCount.FetchSub(1);

            if (usageCount == 0)
            {
                controlChannelNamedEvent.CleanupOnClose = true;
                feedbackChannelNamedEvent.CleanupOnClose = true;

                // Close all the shared config memory regions.
                //
                SharedConfigManager.CleanupOnClose = true;
            }

            base.Dispose(disposing: true);
        }

        private FileDescriptorExchangeServer fileDescriptorExchangeServer;
    }
}
