// -----------------------------------------------------------------------
// <copyright file="DispatchTableNamespaceAttribute.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// Information for CodeGen in which namespace should generate a DispatchTable.
    /// </summary>
    /// <remarks>
    /// Assembly attribute.
    /// </remarks>
    [AttributeUsage(AttributeTargets.Assembly, AllowMultiple = false)]
    public class DispatchTableNamespaceAttribute : BaseCodegenAttribute
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="DispatchTableNamespaceAttribute"/> class.
        /// </summary>
        /// <param name="namespace"></param>
        public DispatchTableNamespaceAttribute(string @namespace)
        {
            Namespace = @namespace;
        }

        /// <summary>
        /// Gets dispatchTable namespace.
        /// </summary>
        public string Namespace { get; }
    }
}
