// -----------------------------------------------------------------------
// <copyright file="MainApp.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

using Grpc.Net.Client;
using GrpcGreeter;

namespace Mlos.Agent.GrpcClient
{
    /// <summary>
    /// Mlos.Agent client test application.
    /// </summary>
    public static class MainApp
    {
        private static async Task Test()
        {
            // The port number(5001) must match the port of the gRPC server.
            //
            using GrpcChannel channel = GrpcChannel.ForAddress("http://localhost:5000");
            var client = new Greeter.GreeterClient(channel);
            EchoReply reply = await client.EchoAsync(
                new EchoRequest
                {
                    Name = "GreeterClient",
                });

            Console.WriteLine("Greeting: " + reply.Message);
            Console.WriteLine("Press any key to exit...");
        }

        /// <summary>
        /// Main function.
        /// </summary>
        public static void Main()
        {
            // This switch must be set before creating the GrpcChannel/HttpClient.
            //
            AppContext.SetSwitch("System.Net.Http.SocketsHttpHandler.Http2UnencryptedSupport", true);

            var res = Test();
            res.Wait();

            // Console.ReadKey();
        }
    }
}
