// -----------------------------------------------------------------------
// <copyright file="TypeMetadataMapper.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen
{
    /// <summary>
    /// Compute hash value for code gen types.
    /// </summary>
    internal class TypeMetadataMapper
    {
        private static uint classCount = 1;

        private static readonly Dictionary<Type, Tuple<ulong, uint>> TypeHashValueMapping = new Dictionary<Type, Tuple<ulong, uint>>();

        /// <summary>
        /// Gets or sets csharp compilation object.
        /// </summary>
        internal static CSharpCompilation Compilation { get; set; }

        /// <summary>
        /// Gets the hash value for the given type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        internal static ulong GetTypeHashValue(Type sourceType)
        {
            if (!TypeHashValueMapping.TryGetValue(sourceType, out var typeEntry))
            {
                // There is no type, we run into code gen issue.
                //
                throw new InvalidOperationException($"Unable to locate cpp type for '{sourceType}' type.");
            }

            return typeEntry.Item1;
        }

        /// <summary>
        /// Gets a type index for the given type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        internal static uint GetTypeIndex(Type sourceType)
        {
            if (!TypeHashValueMapping.TryGetValue(sourceType, out var typeEntry))
            {
                // There is no type, we run into code gen issue.
                //
                throw new InvalidOperationException($"Unable to locate cpp type for '{sourceType}' type.");
            }

            return typeEntry.Item2;
        }

        /// <summary>
        /// Computes and stores hash value for the codegen type.
        /// </summary>
        /// <param name="sourceType"></param>
        internal static void ComputeAndStoreHash(Type sourceType)
        {
            if (!sourceType.IsCodegenType())
            {
                return;
            }

            string structDefinition = Compilation.GetTypeDefinition(sourceType);
            using SHA256 sha256 = SHA256.Create();

            byte[] hashData = sha256.ComputeHash(Encoding.UTF8.GetBytes(structDefinition));
            ulong hashValue = BitConverter.ToUInt64(hashData, 0);

            TypeHashValueMapping.Add(sourceType, new Tuple<ulong, uint>(hashValue, classCount++));
        }
    }
}
