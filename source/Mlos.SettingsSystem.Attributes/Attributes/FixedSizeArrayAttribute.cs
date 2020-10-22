// -----------------------------------------------------------------------
// <copyright file="FixedSizeArrayAttribute.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// An attribute class to mark a C# data structure field as a fixed size array.
    /// </summary>
    /// <remarks>
    /// This makes it possible to specify how to generate the code for a fixed size buffer of non-primitive types.
    /// </remarks>
    [AttributeUsage(AttributeTargets.Field, AllowMultiple = false)]
    public class FixedSizeArrayAttribute : ScalarSettingAttribute
    {
        /// <summary>
        /// Gets the fixed size length of an array field.
        /// </summary>
        public uint Length { get; }

        /// <summary>
        /// Initializes a new instance of the <see cref="FixedSizeArrayAttribute"/> class.
        /// Constructor.
        /// </summary>
        /// <param name="length"></param>
        public FixedSizeArrayAttribute(uint length)
        {
            Length = length;
        }
    }
}
