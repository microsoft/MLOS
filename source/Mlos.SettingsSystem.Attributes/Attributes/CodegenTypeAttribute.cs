// -----------------------------------------------------------------------
// <copyright file="CodegenTypeAttribute.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.Attributes
{
    /// <summary>
    /// An attribute class to mark a C# data structure as a eligible for code generation.
    /// </summary>
    [AttributeUsage(AttributeTargets.Struct | AttributeTargets.Class, AllowMultiple = false)]
    public class CodegenTypeAttribute : BaseCodegenAttribute
    {
    }

    /// <summary>
    /// An attribute to mark a C# data structure as a message type.
    /// </summary>
    public class CodegenMessageAttribute : CodegenTypeAttribute
    {
    }

    /// <summary>
    /// An attribute to mark a C# data structure as a component configuration.
    /// </summary>
    /// <remarks>
    /// Component configuration structures do not allow variable length fields.
    /// </remarks>
    public class CodegenConfigAttribute : CodegenTypeAttribute
    {
    }
}
