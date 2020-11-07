// -----------------------------------------------------------------------
// <copyright file="AssemblyInitializer.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.Core;

using MlosCoreProxy = Proxy.Mlos.Core;
using MlosUnitTestProxy = Proxy.Mlos.UnitTest;

namespace Mlos.UnitTest
{
    public static class AssemblyInitializer
    {
        static AssemblyInitializer()
        {
            MlosUnitTestProxy.WideStringViewArray.Callback = RunA;
            MlosUnitTestProxy.Line.Callback = RunB;
            MlosUnitTestProxy.UpdateConfigTestMessage.Callback = UpdateConfigTestMessage;
        }

        internal static void RunA(MlosUnitTestProxy.WideStringViewArray wideStringArrayProxy)
        {
            var a = wideStringArrayProxy.Id;
            var b = wideStringArrayProxy.Strings[0].Value;
            var c = wideStringArrayProxy.Strings[1].Value;
            var d = wideStringArrayProxy.Strings[2].Value;
            var e = wideStringArrayProxy.Strings[3].Value;
            var f = wideStringArrayProxy.Strings[4].Value;
        }

        internal static void RunB(MlosUnitTestProxy.Line line)
        {
            var a = line.Colors[0];
            var b = line.Colors[0];
            var c = line.Points[0];
        }

        internal static void UpdateConfigTestMessage(MlosUnitTestProxy.UpdateConfigTestMessage msg)
        {
            // Update config.
            //
            var channelReaderStats = MlosContext.Instance.SharedConfigManager.Lookup<MlosCoreProxy.ChannelReaderStats>().Config;
            channelReaderStats.SpinCount++;
        }
    }
}
