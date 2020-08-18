// -----------------------------------------------------------------------
// <copyright file="GreeterService.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Threading.Tasks;

using Grpc.Core;
using GrpcGreeter;

namespace Mlos.Agent.GrpcServer
{
    public class GreeterService : global::GrpcGreeter.Greeter.GreeterBase
    {
        public override Task<EchoReply> Echo(EchoRequest request, ServerCallContext context)
        {
            return Task.FromResult(new EchoReply
            {
                Message = "Hello " + request.Name,
            });
        }
    }
}
