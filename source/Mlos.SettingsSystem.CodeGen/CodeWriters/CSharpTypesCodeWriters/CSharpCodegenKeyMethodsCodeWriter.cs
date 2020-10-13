// -----------------------------------------------------------------------
// <copyright file="CSharpCodegenKeyMethodsCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpObjectExchangeCodeWriters
{
    /// <summary>
    /// Code writer class for CSharp ICodegenKey implementation.
    /// </summary>
    /// <remarks>
    /// Writes all properties.
    /// </remarks>
    internal class CSharpCodegenKeyMethodsCodeWriter : CSharpCodeWriter
    {
        /// <summary>
        /// Gets or sets name of dispatch table base index variable.
        /// </summary>
        private string DispatchTableBaseIndexVariableName { get; set; }

        /// <summary>
        /// Initializes a new instance of the <see cref="CSharpCodegenKeyMethodsCodeWriter"/> class.
        /// </summary>
        /// <remarks>
        /// Get DispatchTable namespace from the custom assembly attribute.
        /// </remarks>
        /// <param name="sourceTypesAssembly"></param>
        public CSharpCodegenKeyMethodsCodeWriter(Assembly sourceTypesAssembly)
        {
            DispatchTableBaseIndexVariableName = sourceTypesAssembly.GetDispatchTableBaseIndexVariableName();
        }

        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType() && sourceType.HasPrimaryKey();

        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            WriteLine($"namespace {@namespace}");
            WriteLine("{");

            ++IndentationLevel;
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            --IndentationLevel;
            WriteLine($"}} // end namespace {@namespace}");

            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            string typeName = sourceType.Name;
            string typeFullType = $"global::{sourceType.GetTypeFullName()}";
            string proxyTypeFullName = $"{Constants.ProxyNamespace}.{sourceType.GetTypeFullName()}";

            WriteBlock($@"
                public partial struct CodegenKey : ICodegenKey<{typeFullType}, {typeFullType}.CodegenKey, {proxyTypeFullName}>
                {{
                    public uint GetKeyHashValue<THash>()
                        where THash : global::Mlos.Core.Collections.IHash<uint>
                    {{
                        THash hash = default(THash);
                        uint hashValue = hash.GetHashValue(((global::Mlos.Core.ICodegenKey)this).CodegenTypeHash());");

            IndentationLevel += 2;
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            WriteLine();
            WriteLine("return hashValue;");
            IndentationLevel--;

            WriteLine("}");
            WriteLine();

            uint typeIndex = TypeMetadataMapper.GetTypeIndex(sourceType);

            ulong typeHashValue = TypeMetadataMapper.GetTypeHashValue(sourceType);

            WriteBlock($@"
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                uint global::Mlos.Core.ICodegenKey.CodegenTypeIndex() => {typeIndex} + {DispatchTableBaseIndexVariableName};");

            WriteBlock($@"
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                ulong global::Mlos.Core.ICodegenKey.CodegenTypeHash() => 0x{typeHashValue:x};");

            IndentationLevel--;

            WriteLine("}");
            WriteLine();

            WriteCloseTypeDeclaration(sourceType);
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            if (!cppField.FieldInfo.IsPrimaryKey())
            {
                // The field is not a primary key, ignore it.
                //
                return;
            }

            string fieldName = cppField.FieldInfo.Name;

            WriteLine($"hashValue = hash.CombineHashValue(hashValue, this.{fieldName});");
        }
    }
}
