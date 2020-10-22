// -----------------------------------------------------------------------
// <copyright file="CppObjectDeserializeFunctionCallbackCodeWriter.cs" company="Microsoft Corporation">
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
    /// Generates an events handlers functions.
    /// Dispatch received event using std::functions.
    /// </summary>
    /// <remarks>
    /// Calling callback using std::function has cost. Main purpose is test code, where we can change the handler code.
    /// </remarks>
    internal class CppObjectDeserializeFunctionCallbackCodeWriter : CppTypeTableCodeWriter
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="CppObjectDeserializeFunctionCallbackCodeWriter"/> class.
        /// </summary>
        /// <param name="sourceTypesAssembly"></param>
        public CppObjectDeserializeFunctionCallbackCodeWriter(Assembly sourceTypesAssembly)
            : base(sourceTypesAssembly)
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
            // Deserialize callbacks.
            //
            WriteBlock(@$"
                // Provide a default implementation of deserialize handlers.
                // To deserialize type handler will call a dedicated callback.
                // This allows change handler logic in runtime.
                // Using callbacks introduces performance overhead and should be used only in test code.
                //
                namespace {Constants.ObjectDeserializationCallbackNamespace}
                {{");

            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            // Close ObjectDeserializeCallback namespace.
            //
            IndentationLevel--;
            WriteLine($"}} // end namespace {Constants.ObjectDeserializationCallbackNamespace}");
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
            string cppTypeFullName = CppTypeMapper.GetCppFullTypeName(sourceType);
            string cppProxyTypeFullName = CppTypeMapper.GetCppProxyFullTypeName(sourceType);

            string cppTypeDeserializeCallback = $"::{Constants.ObjectDeserializationCallbackNamespace}{cppTypeFullName}_Callback";

            WriteBlock($@"
                template <>
                inline void Deserialize<{cppProxyTypeFullName}>({cppProxyTypeFullName}&& obj)
                {{
                    if ({cppTypeDeserializeCallback}) {cppTypeDeserializeCallback}(std::move(obj));
                }}");
        }

        /// <inheritdoc />
        public override string FilePostfix => "_callbacks.h";
    }
}
