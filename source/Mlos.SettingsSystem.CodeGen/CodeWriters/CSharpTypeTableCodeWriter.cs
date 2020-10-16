// -----------------------------------------------------------------------
// <copyright file="CSharpTypeTableCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters
{
    /// <summary>
    /// Abstract class for code writes which create a single table from all type types.
    /// </summary>
    /// <remarks>
    /// Used by reflection and handlers code writers.
    /// </remarks>
    internal abstract class CSharpTypeTableCodeWriter : CodeWriter
    {
        /// <summary>
        /// Gets namespace used to create DispatchTable.
        /// </summary>
        protected string DispatchTableCSharpNamespace { get; private set; }

        /// <summary>
        /// Initializes a new instance of the <see cref="CSharpTypeTableCodeWriter"/> class.
        /// </summary>
        /// <remarks>
        /// Get DispatchTable namespace from the custom assembly attribute.
        /// </remarks>
        /// <param name="sourceTypesAssembly"></param>
        protected CSharpTypeTableCodeWriter(Assembly sourceTypesAssembly)
        {
            // Get the global name of the dispatch table.
            // Used primarily for defining a dispatch base table index.
            //
            DispatchTableNamespaceAttribute dispatchTableCSharpNamespaceAttribute = sourceTypesAssembly.GetCustomAttribute<DispatchTableNamespaceAttribute>();

            DispatchTableCSharpNamespace = dispatchTableCSharpNamespaceAttribute?.Namespace;
        }

        /// <inheritdoc />
        public sealed override void WriteOpenTypeNamespace(string @namespace)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public sealed override void WriteCloseTypeNamespace(string @namespace)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public sealed override void BeginVisitType(Type sourceType)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public sealed override void VisitField(CppField cppField)
        {
            // Do not generate information about structure fields.
            //
        }

        /// <inheritdoc />
        public sealed override void WriteComments(CodeComment codeComment)
        {
            // No comments
            //
        }

        /// <summary>
        /// Beginning of a global namespace.
        /// </summary>
        protected void WriteGlobalBeginNamespace()
        {
            // Write using statements.
            //
            WriteLine("using Mlos.Core;");
            WriteLine();

            if (!string.IsNullOrEmpty(DispatchTableCSharpNamespace))
            {
                WriteLine($"namespace {DispatchTableCSharpNamespace}");
                WriteLine("{");

                IndentationLevel++;
            }
        }

        /// <summary>
        /// End global namespace.
        /// </summary>
        protected void WriteGlobalEndNamespace()
        {
            if (!string.IsNullOrEmpty(DispatchTableCSharpNamespace))
            {
                IndentationLevel--;

                WriteLine("}");
            }
        }

        /// <summary>
        /// Gets or sets total number of classes.
        /// </summary>
        protected int ClassCount { get; set; }

        /// <inheritdoc />
        public override string FilePostfix => "_base.cs";
    }
}
