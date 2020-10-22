// -----------------------------------------------------------------------
// <copyright file="CppObjectDeserializeEntryCountCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters
{
    /// <summary>
    /// Code writer class which generates a dispatch table with object deserialize handlers.
    /// </summary>
    /// <remarks>
    /// Generates a static table containing type information.
    /// </remarks>
    internal class CppObjectDeserializeEntryCountCodeWriter : CppTypeTableCodeWriter
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="CppObjectDeserializeEntryCountCodeWriter"/> class.
        /// </summary>
        /// <param name="sourceTypesAssembly"></param>
        public CppObjectDeserializeEntryCountCodeWriter(Assembly sourceTypesAssembly)
            : base(sourceTypesAssembly)
        {
        }

        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        /// <remarks>
        /// Proxy structures are defined in namespace Proxy.
        /// </remarks>
        public override void WriteBeginFile()
        {
            WriteGlobalBeginNamespace();

            // Objects dispatch table.
            //
            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            // Write how many elements are present in the dispatch table.
            //
            WriteLine($"constexpr std::size_t DispatchTableElementCount() {{ return {ClassCount}; }}");

            // Close EventReceiver namespace.
            //
            IndentationLevel--;

            WriteGlobalEndNamespace();

            WriteLine();
        }

        /// <inheritdoc />
        /// <param name="sourceType"></param>
        public override void BeginVisitType(Type sourceType) => ++ClassCount;
    }
}
