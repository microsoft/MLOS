// -----------------------------------------------------------------------
// <copyright file="MlosAgentServer.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Microsoft.Extensions.Hosting;

using Mlos.Core;

using MlosOptimizer = Mlos.Model.Services.Client.BayesianOptimizer;

namespace Mlos.Agent.Server
{
    /// <summary>
    /// The MlosAgentServer acts as a simple external agent and shim helper to
    /// wrap the various communication channels (shared memory to/from the smart
    /// component, grpc to the optimizer, grpc from the notebooks).
    /// </summary>
    public static class MlosAgentServer
    {
        /// <summary>
        /// Starts a grpc server listening for requests from the notebook to drive
        /// the agent interactively.
        /// </summary>
        /// <param name="args">unused.</param>
        /// <returns>grpc server task.</returns>
        public static IHostBuilder CreateHostBuilder(string[] args) =>
            Host.CreateDefaultBuilder(args)
                .ConfigureWebHostDefaults(webBuilder =>
                {
                    webBuilder.ConfigureKestrel(options =>
                    {
                        // Setup a HTTP/2 endpoint without TLS.
                        //
                        options.ListenAnyIP(5000, o => o.Protocols = HttpProtocols.Http2);
                    });
                    webBuilder.UseStartup<GrpcServer.Startup>();
                });

        /// <summary>
        /// The main external agent server.
        /// </summary>
        /// <param name="args">command line arguments.</param>
        public static void Main(string[] args)
        {
            string executableFilePath;
            Uri optimizerAddressUri;
            string settingsRegistryPath;
            CliOptionsParser.ParseArgs(args, out executableFilePath, out optimizerAddressUri, out settingsRegistryPath);

            // Check for the executable before setting up any shared memory to
            // reduce cleanup issues.
            //
            if (!string.IsNullOrEmpty(executableFilePath) && !File.Exists(executableFilePath))
            {
                throw new FileNotFoundException($"ERROR: --executable '{executableFilePath}' does not exist.");
            }

            if (!string.IsNullOrEmpty(settingsRegistryPath))
            {
                // #TODO temporary hack
                //
                Environment.SetEnvironmentVariable("MLOS_SETTINGS_REGISTRY_PATH", settingsRegistryPath);
            }

            Console.WriteLine("Mlos.Agent.Server");
            TargetProcessManager targetProcessManager = null;

            // In the active learning mode, create a new shared memory map before running the target process.
            // On Linux, we unlink existing shared memory map, if they exist.
            // If the agent is not in the active learning mode, create new or open existing to communicate with the target process.
            //
            using MlosContext mlosContext = (executableFilePath != null)
                ? InterProcessMlosContext.Create()
                : InterProcessMlosContext.CreateOrOpen();

            // Connect to gRpc optimizer only if user provided an address in the command line.
            //
            if (optimizerAddressUri != null)
            {
                Console.WriteLine("Connecting to the Mlos.Optimizer");

                // This switch must be set before creating the GrpcChannel/HttpClient.
                //
                AppContext.SetSwitch("System.Net.Http.SocketsHttpHandler.Http2UnencryptedSupport", true);

                // This populates a variable for the various settings registry
                // callback handlers to use (by means of their individual
                // AssemblyInitializers) to know how they can connect with the
                // optimizer.
                //
                // See Also: AssemblyInitializer.cs within the SettingsRegistry
                // assembly project in question.
                //
                mlosContext.OptimizerFactory = new MlosOptimizer.BayesianOptimizerFactory(optimizerAddressUri);
            }

            using var mainAgent = new MainAgent();
            mainAgent.InitializeSharedChannel(mlosContext);

            // Active learning mode.
            //
            // TODO: In active learning mode the MlosAgentServer can control the
            // workload against the target component.
            //
            if (executableFilePath != null)
            {
                Console.WriteLine($"Starting {executableFilePath}");
                targetProcessManager = new TargetProcessManager(executableFilePath: executableFilePath);
                targetProcessManager.StartTargetProcess();
            }
            else
            {
                Console.WriteLine("No executable given to launch.  Will wait for agent to connect independently.");
            }

            var cancellationTokenSource = new CancellationTokenSource();

            Task grpcServerTask = CreateHostBuilder(Array.Empty<string>()).Build().RunAsync(cancellationTokenSource.Token);

            // Start the MainAgent message processing loop as a background thread.
            //
            // In MainAgent.RunAgent we loop on the shared memory control and
            // telemetry channels looking for messages and dispatching them to
            // their registered callback handlers.
            //
            // The set of recognized messages is dynamically registered using
            // the RegisterSettingsAssembly method which is called through the
            // handler for the RegisterAssemblyRequestMessage.
            //
            // Once registered, the SettingsAssemblyManager uses reflection to
            // search for an AssemblyInitializer inside those assemblies and
            // executes it in order to setup the message handler callbacks
            // within the agent.
            //
            // See Also: AssemblyInitializer.cs within the SettingsRegistry
            // assembly project in question.
            //
            Console.WriteLine("Starting Mlos.Agent");
            Task mlosAgentTask = Task.Factory.StartNew(
                () => mainAgent.RunAgent(),
                CancellationToken.None,
                TaskCreationOptions.LongRunning,
                TaskScheduler.Current);

            Task waitForTargetProcessTask = Task.Factory.StartNew(
                () =>
                {
                    if (targetProcessManager != null)
                    {
                        targetProcessManager.WaitForTargetProcessToExit();
                        targetProcessManager.Dispose();
                        mainAgent.UninitializeSharedChannel();
                    }
                },
                CancellationToken.None,
                TaskCreationOptions.LongRunning,
                TaskScheduler.Current);

            Console.WriteLine("Waiting for Mlos.Agent to exit");

            while (true)
            {
                Task.WaitAny(mlosAgentTask, waitForTargetProcessTask);

                if (mlosAgentTask.IsFaulted && targetProcessManager != null && !waitForTargetProcessTask.IsCompleted)
                {
                    // MlosAgentTask has failed, however the target process is still active.
                    // Terminate the target process and continue shutdown.
                    //
                    targetProcessManager.TerminateTargetProcess();
                    continue;
                }

                if (mlosAgentTask.IsCompleted && waitForTargetProcessTask.IsCompleted)
                {
                    // MlosAgentTask is no longer processing messages, and target process does no longer exist.
                    // Shutdown the agent.
                    //
                    break;
                }
            }

            int exitCode = 0;

            // Print any exceptions if occurred.
            //
            if (mlosAgentTask.Exception != null)
            {
                Console.WriteLine($"Exception: {mlosAgentTask.Exception}");
                exitCode |= 1;
            }

            if (waitForTargetProcessTask.Exception != null)
            {
                Console.WriteLine($"Exception: {waitForTargetProcessTask.Exception}");
                exitCode |= 2;
            }

            // Perform some cleanup.
            //
            waitForTargetProcessTask.Dispose();

            mlosAgentTask.Dispose();

            targetProcessManager?.Dispose();

            cancellationTokenSource.Cancel();
            grpcServerTask.Wait();

            grpcServerTask.Dispose();
            cancellationTokenSource.Dispose();

            Console.WriteLine("Mlos.Agent exited.");

            Environment.Exit(exitCode);
        }
    }
}
