// -----------------------------------------------------------------------
// <copyright file="BaseCodegenFieldAttribute.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// Base Mlos Setting attribute.
    /// To be applied to scalar field member types inside a SettingsRegistry.
    /// </summary>
    [AttributeUsage(AttributeTargets.Field, AllowMultiple = false)]
    public abstract class BaseCodegenFieldAttribute : BaseCodegenAttribute
    {
    }
}
