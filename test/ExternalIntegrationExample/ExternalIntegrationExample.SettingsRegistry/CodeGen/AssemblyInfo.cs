// -----------------------------------------------------------------------
// <copyright file="AssemblyInfo.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------
//
// This file provides optional assembly wide annotations for both the codegen output and the
// compiled SettingsRegistry assembly dll.

using System.Runtime.CompilerServices;

using Mlos.SettingsSystem.Attributes;

// This is ths namespace used for the C++ codegen output for the messages and settings in this
// Settings Registry.
[assembly: DispatchTableNamespace(@namespace: "ExternalIntegrationExample")]
