// -----------------------------------------------------------------------
// <copyright file="AlignAttribute.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// An attribute class to mark the alignment for a codegen structs and fields.
    /// </summary>
    [AttributeUsage(AttributeTargets.Struct | AttributeTargets.Field, AllowMultiple = false)]
    public class AlignAttribute : BaseCodegenFieldAttribute
    {
        /// <summary>
        /// Gets the alignment size.
        /// </summary>
        public uint Size { get; }

        /// <summary>
        /// Initializes a new instance of the <see cref="AlignAttribute"/> class.
        /// </summary>
        /// <param name="size">The alignment size for the field.</param>
        public AlignAttribute(uint size)
        {
            Size = size;
        }
    }
}
