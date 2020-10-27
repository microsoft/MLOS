// -----------------------------------------------------------------------
// <copyright file="ScalarSettingAttribute.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// An attribute class to mark a C# field as a Setting for codegen purposes.
    /// </summary>
    [AttributeUsage(AttributeTargets.Field, AllowMultiple = false)]
    public class ScalarSettingAttribute : BaseCodegenFieldAttribute
    {
        // TODO: default ranges, test correlation, telemetry, identifies, etc.
        // TODO: does this still make sense ??
        //

        /// <summary>
        /// Gets a value indicating whether is primary key.
        /// </summary>
        public bool IsPrimaryKey { get; private set; }

        /// <summary>
        /// Initializes a new instance of the <see cref="ScalarSettingAttribute"/> class.
        /// </summary>
        /// <param name="isPrimaryKey">If true the field is part of the shared config primary key.</param>
        public ScalarSettingAttribute(bool isPrimaryKey = false)
        {
            IsPrimaryKey = isPrimaryKey;
        }
    }
}
