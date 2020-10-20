// -----------------------------------------------------------------------
// <copyright file="CppObjectDeserializeRuntimeCallbackCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters
{
    /// <summary>
    /// Generates an events handlers functions.
    /// Dispatch received event using std::functions.
    /// </summary>
    /// <remarks>
    /// Calling callback using std::function has cost. Main purpose is test code, where we can change the handler code.
    /// </remarks>
    internal class CppObjectDeserializeRuntimeCallbackCodeWriter : CppCodeWriter
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="CppObjectDeserializeRuntimeCallbackCodeWriter"/> class.
        /// </summary>
        public CppObjectDeserializeRuntimeCallbackCodeWriter()
        {
        }

        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        /// <remarks>
        /// Write default implementation of deserialize handlers.
        /// </remarks>
        public override void WriteBeginFile()
        {
            WriteLine($@"#pragma once");
            WriteLine();

            // Deserialize callbacks.
            //
            WriteBlock($@"
                // Provide a default implementation of deserialize handlers.
                // On deserialize type, handler will call a dedicated callback.
                // This allows change handler logic in runtime.
                // Using callbacks introduces performance overhead and should be used only in test code.
                //
                namespace {Constants.ObjectDeserializationCallbackNamespace}
                {{");

            WriteLine();

            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            // Close ObjectDeserializeCallback namespace.
            //
            IndentationLevel--;
            WriteLine($"}}  // end namespace {Constants.ObjectDeserializationCallbackNamespace}");
            WriteLine();
        }

        /// <summary>
        /// For a new structure, create a entry in metadata table.
        /// </summary>
        /// <param name="sourceType"></param>
        public override void BeginVisitType(Type sourceType)
        {
            // Receiver is using proxy struct.
            //
            string cppProxyTypeFullName = CppTypeMapper.GetCppProxyFullTypeName(sourceType);

            // Use type name, as we are already in type namespace.
            //
            string cppTypeNameAsField = $"{sourceType.Name}_Callback";

            WriteLine($"__declspec(selectany) std::function<void ({cppProxyTypeFullName}&&)> {cppTypeNameAsField} = nullptr;");
            WriteLine();
        }

        /// <inheritdoc/>
        public override void VisitField(CppField cppField)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override void EndVisitType(Type sourceType)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override void WriteComments(CodeComment codeComment)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override string FilePostfix => "_callbacks.h";
    }
}
