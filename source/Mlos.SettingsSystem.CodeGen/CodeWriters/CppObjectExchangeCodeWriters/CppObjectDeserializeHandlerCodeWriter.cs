// -----------------------------------------------------------------------
// <copyright file="CppObjectDeserializeHandlerCodeWriter.cs" company="Microsoft Corporation">
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
    internal class CppObjectDeserializeHandlerCodeWriter : CppTypeTableCodeWriter
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="CppObjectDeserializeHandlerCodeWriter"/> class.
        /// </summary>
        /// <param name="sourceTypesAssembly"></param>
        public CppObjectDeserializeHandlerCodeWriter(Assembly sourceTypesAssembly)
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

            // Define a global dispatch table.
            //
            WriteLine("__declspec(selectany) ::Mlos::Core::DispatchEntry DispatchTable[] = ");
            WriteLine("{");

            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            // Close DispatchTable.
            //
            IndentationLevel--;
            WriteLine("};");
            WriteLine();

            // Close EventReceiver namespace.
            //
            IndentationLevel--;

            WriteGlobalEndNamespace();

            WriteLine();
        }

        /// <summary>
        /// For each serializable structure, create an entry with deserialization handler in the dispatch callback table.
        /// </summary>
        /// <param name="sourceType"></param>
        public override void BeginVisitType(Type sourceType)
        {
            string cppTypeFullName = CppTypeMapper.GetCppFullTypeName(sourceType);
            string cppProxyTypeFullName = CppTypeMapper.GetCppProxyFullTypeName(sourceType);

            WriteBlock(@$"
                ::Mlos::Core::DispatchEntry
                {{
                    {Constants.TypeMetadataInfoNamespace}::CodegenTypeHash<{cppTypeFullName}>(),
                    [](::Mlos::Core::BytePtr&& buffer, int frameLength)
                    {{
                        {cppProxyTypeFullName} recvObjectProxy(buffer);
                        bool isValid = {Constants.ObjectSerializationNamespace}::VerifyVariableData(recvObjectProxy, frameLength);
                        if (isValid)
                        {{
                            ::{Constants.ObjectDeserializationCallbackNamespace}::Deserialize(std::move(recvObjectProxy));
                        }}

                        return isValid;
                    }}
                }},");
        }

        /// <inheritdoc />
        public override string FilePostfix => "_dispatch.h";
    }
}
