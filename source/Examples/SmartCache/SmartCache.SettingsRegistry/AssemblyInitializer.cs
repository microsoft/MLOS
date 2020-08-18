// -----------------------------------------------------------------------
// <copyright file="AssemblyInitializer.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Runtime.InteropServices;

using Mlos.Core;
using SmartCache;

using SmartCacheProxy = Proxy.SmartCache;

namespace SmartCache
{
    public static class AssemblyInitializer
    {
        static AssemblyInitializer()
        {
            SmartCacheProxy.CacheRequestEventMessage.Callback = CacheRequestEventMessageHandler;
        }

        private static void CacheRequestEventMessageHandler(SmartCacheProxy.CacheRequestEventMessage message)
        {
        }
    }
}