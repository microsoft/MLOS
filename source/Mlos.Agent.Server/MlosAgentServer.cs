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
        private static IHostBuilder CreateHostBuilder(string[] args) =>
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
        /// <returns>Returns exit code.</returns>
        public static int Main(string[] args)
        {
            CliOptionsParser.CliOptions parserOptions = CliOptionsParser.ParseArgs(args);

            if (!string.IsNullOrEmpty(parserOptions.ExperimentFilePath) && !File.Exists(parserOptions.ExperimentFilePath))
            {
                throw new FileNotFoundException($"ERROR: --experiment '{parserOptions.ExperimentFilePath}' does not exist.");
            }

            if (!string.IsNullOrEmpty(parserOptions.SettingsRegistryPath))
            {
                // #TODO temporary hack
                //
                Environment.SetEnvironmentVariable("MLOS_SETTINGS_REGISTRY_PATH", parserOptions.SettingsRegistryPath);
            }

            Console.WriteLine("Mlos.Agent.Server");

            // Active learning mode.
            //
            // TODO: In active learning mode the MlosAgentServer can control the
            // workload against the target component.
            //
            TargetProcessManager targetProcessManager = null;
            if (parserOptions.Executable != null)
            {
                Console.WriteLine($"Starting: '{parserOptions.Executable}'");
                targetProcessManager = new TargetProcessManager(executableFilePath: parserOptions.Executable);
                targetProcessManager.StartTargetProcess();

                Console.WriteLine($"Launched process: '{Path.GetFileName(parserOptions.Executable)}'");
            }
            else
            {
                Console.WriteLine("No executable given to launch.  Will wait for agent to connect independently.");
            }

            // Create a Mlos context.
            //
            using MlosContext mlosContext = MlosContextFactory.Create();

            // Connect to gRpc optimizer only if user provided an address in the command line.
            //
            if (parserOptions.OptimizerUri != null)
            {
                Console.WriteLine("Connecting to the Mlos.Optimizer");

                // This switch must be set before creating the GrpcChannel/HttpClient.
                //
                AppContext.SetSwitch("System.Net.Http.SocketsHttpHandler.Http2UnencryptedSupport", true);

                // This populates a variable for the various settings registry
                // callback handlers to use (by means of their individual
                // ExperimentSession instances) to know how they can connect with
                // the optimizer.
                //
                // See SmartCacheExperimentSession.cs for an example.
                //
                mlosContext.OptimizerFactory = new MlosOptimizer.BayesianOptimizerFactory(parserOptions.OptimizerUri);
            }

            var experimentSessionManager = new ExperimentSessionManager(mlosContext);

            using var mainAgent = new MainAgent();
            mainAgent.InitializeSharedChannel(mlosContext);

            // If specified, load the experiment assembly.
            //
            if (!string.IsNullOrEmpty(parserOptions.ExperimentFilePath))
            {
                experimentSessionManager.LoadExperiment(parserOptions.ExperimentFilePath);
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
            // Once registered, the ExperimentSessionManager can creates an
            // instance of the requested ExperimentSession in order to setup the
            // message handler callbacks for the components messages within the
            // agent.
            //
            // See SmartCacheExperimentSession.cs for an example.
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

            return exitCode;
        }
    }
}
