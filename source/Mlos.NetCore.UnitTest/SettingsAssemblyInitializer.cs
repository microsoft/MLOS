// -----------------------------------------------------------------------
// <copyright file="SettingsAssemblyInitializer.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.Core;
using Mlos.UnitTest;

namespace Mlos.NetCore.UnitTest
{
    internal static class SettingsAssemblyInitializer
    {
        private static readonly SettingsAssemblyManager SettingsAssemblyManager = new SettingsAssemblyManager();

        static SettingsAssemblyInitializer()
        {
            // Load the registry settings assemblies.
            //
            SettingsAssemblyManager.RegisterAssembly(typeof(MlosContext).Assembly);
            SettingsAssemblyManager.RegisterAssembly(typeof(AssemblyInitializer).Assembly);
        }

        public static DispatchEntry[] GetGlobalDispatchTable()
        {
            return SettingsAssemblyManager.GetGlobalDispatchTable();
        }
    }
}
