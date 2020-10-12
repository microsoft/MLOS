// -----------------------------------------------------------------------
// <copyright file="SettingsAssemblyManager.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.Core
{
    /// <summary>
    /// Settings assembly manager.
    /// Manages codegen type dispatch and and deserialize callbacks tables.
    /// </summary>
    public class SettingsAssemblyManager
    {
        /// <summary>
        /// Registers settings assembly.
        /// </summary>
        /// <param name="assembly"></param>
        public void RegisterAssembly(Assembly assembly)
        {
            RegisterAssembly(assembly, CodegenTypeCount);
        }

        /// <summary>
        /// Registers settings assembly.
        /// </summary>
        /// <remarks>Update deserialize and dispatch tables.</remarks>
        /// <param name="assembly"></param>
        /// <param name="dispatchTableBaseIndex"></param>
        public void RegisterAssembly(Assembly assembly, uint dispatchTableBaseIndex)
        {
            // Ensure the assembly base index is correct.
            //
            if (settingsAssemblies.ContainsKey(assembly.FullName))
            {
                uint existingDispatchTableBaseIndex = settingsAssemblies[assembly.FullName];

                if (existingDispatchTableBaseIndex == dispatchTableBaseIndex)
                {
                    // Assembly is already registered.
                    //
                    return;
                }

                throw new InvalidOperationException($"Trying to register settings assembly {assembly.FullName} {existingDispatchTableBaseIndex} with different dispatch table base index {dispatchTableBaseIndex}.");
            }

            if (dispatchTableBaseIndex != CodegenTypeCount)
            {
                throw new InvalidOperationException($"Register settings assembly {assembly.FullName} failed.");
            }

            // Get the dispatcher table.
            //
            DispatchTableNamespaceAttribute dispatchTableNamespaceAttribute = assembly.GetCustomAttribute<DispatchTableNamespaceAttribute>();

            // Update the assembly dispatch table base index.
            //
            string typeName = $"{dispatchTableNamespaceAttribute.Namespace}.ObjectDeserializeHandler";
            Type objectDeserializeHandler = assembly.GetType(typeName);
            FieldInfo fieldInfo = objectDeserializeHandler.GetField("DispatchTableBaseIndex", BindingFlags.Public | BindingFlags.Static);
            fieldInfo.SetValue(null, CodegenTypeCount);

            DispatchEntry[] dispatchTable = (DispatchEntry[])objectDeserializeHandler.GetField("DispatchTable", BindingFlags.Static | BindingFlags.Public).GetValue(null);
            DeserializeEntry[] deserializationTable = (DeserializeEntry[])objectDeserializeHandler.GetField("DeserializationCallbackTable", BindingFlags.Static | BindingFlags.Public).GetValue(null);

            // Init module.
            //
            Type callbackHandlersType = assembly.GetType($"{dispatchTableNamespaceAttribute.Namespace}.AssemblyInitializer");

            if (callbackHandlersType != null)
            {
                System.Runtime.CompilerServices.RuntimeHelpers.RunClassConstructor(callbackHandlersType.TypeHandle);
            }

            // Update global dispatch table.
            //
            globalDispatchTable.AddRange(dispatchTable);
            globalDeserializationTable.AddRange(deserializationTable);

            // Add settings assembly.
            //
            settingsAssemblies.Add(assembly.FullName, dispatchTableBaseIndex);
        }

        /// <summary>
        /// Gets number of declared codegen types.
        /// </summary>
        public uint CodegenTypeCount => (uint)globalDeserializationTable.Count;

        /// <summary>
        /// Returns a global deserialization callback table.
        /// </summary>
        /// <returns></returns>
        public DeserializeEntry[] GetGlobalDeserializationTable() => globalDeserializationTable.ToArray();

        /// <summary>
        /// Returns a global dispatch callback table.
        /// </summary>
        /// <returns></returns>
        public DispatchEntry[] GetGlobalDispatchTable() => globalDispatchTable.ToArray();

        /// <summary>
        /// Settings registry assemblies.
        /// </summary>
        /// <remarks>
        /// We keep assembly and base dispatch table index.
        /// </remarks>
        private readonly Dictionary<string, uint> settingsAssemblies = new Dictionary<string, uint>();

        private readonly List<DeserializeEntry> globalDeserializationTable = new List<DeserializeEntry>();

        private readonly List<DispatchEntry> globalDispatchTable = new List<DispatchEntry>();
    }
}
