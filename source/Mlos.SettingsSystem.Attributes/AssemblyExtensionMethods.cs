// -----------------------------------------------------------------------
// <copyright file="AssemblyExtensionMethods.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// Set of public Assembly extension methods.
    /// </summary>
    public static class AssemblyExtensionMethods
    {
        /// <summary>
        /// Returns instance to ObjectDeserializeHandler.DispatchTableBaseIndex.
        /// </summary>
        /// <param name="assembly"></param>
        /// <returns></returns>
        internal static string GetDispatchTableBaseIndexVariableName(this Assembly assembly)
        {
            DispatchTableNamespaceAttribute dispatchTableCSharpNamespaceAttribute = assembly.GetCustomAttribute<DispatchTableNamespaceAttribute>();

            string dispatchTableCSharpNamespace = dispatchTableCSharpNamespaceAttribute?.Namespace;

            return "global::" +
                (string.IsNullOrEmpty(dispatchTableCSharpNamespace) ? string.Empty : $"{dispatchTableCSharpNamespace}.") +
                "ObjectDeserializeHandler.DispatchTableBaseIndex";
        }
    }
}
