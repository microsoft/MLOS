// -----------------------------------------------------------------------
// <copyright file="AssemblyInfo.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

/// <remarks>
/// This file provides optional assembly wide annotations for both the codegen output and the
/// compiled SettingsRegistry assembly dll.
/// </remarks>

using System.Runtime.CompilerServices;

using Mlos.SettingsSystem.Attributes;

/// <remarks>
/// This is ths namespace used for the C++ codegen output for the messages and settings in this
/// Settings Registry.
/// </remarks>
[assembly: DispatchTableNamespace(@namespace: "ExternalIntegrationExample")]
