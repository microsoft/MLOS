// -----------------------------------------------------------------------
// <copyright file="CSharpObjectCodegenTypeCodeWriter.cs" company="Microsoft Corporation">
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
    /// Code writer class for CSharp ICodegenType implementation.
    /// </summary>
    /// <remarks>
    /// Writes all properties.
    /// </remarks>
    internal class CSharpObjectCodegenTypeCodeWriter : CSharpCodeWriter
    {
        /// <summary>
        /// Gets or sets namespace used to create DispatchTable.
        /// </summary>
        private string DispatchTableCSharpNamespace { get; set; }

        /// <summary>
        /// Initializes a new instance of the <see cref="CSharpObjectCodegenTypeCodeWriter"/> class.
        /// </summary>
        /// <remarks>
        /// Get DispatchTable namespace from the custom assembly attribute.
        /// </remarks>
        /// <param name="sourceTypesAssembly"></param>
        public CSharpObjectCodegenTypeCodeWriter(Assembly sourceTypesAssembly)
        {
            // Get the global name of the dispatch table.
            // Used primarily for defining a dispatch base table index.
            //
            var dispatchTableCSharpNamespaceAttribute = sourceTypesAssembly.GetCustomAttribute<DispatchTableNamespaceAttribute>();

            DispatchTableCSharpNamespace = dispatchTableCSharpNamespaceAttribute?.Namespace;
        }

        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType.DeclaringType);

            string typeName = sourceType.Name;
            string typeFullType = $"global::{sourceType.GetTypeFullName()}";
            string proxyFullName = $"{Constants.ProxyNamespace}.{sourceType.GetTypeFullName()}";
            string typeRepresentation = sourceType.IsClass ? "class" : "struct";

            WriteBlock($@"
                partial {typeRepresentation} {typeName} : global::Mlos.Core.ICodegenType<{typeFullType}, {proxyFullName}>
                {{
                    public uint GetKeyHashValue<THash>()
                        where THash : global::Mlos.Core.Collections.IHash<uint>
                    {{
                        THash hash = default(THash);
                        uint hashValue = hash.GetHashValue(((global::Mlos.Core.ICodegenType)this).CodegenTypeHash());");

            IndentationLevel += 2;
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            CppType cppType = CppTypeMapper.GetCppType(sourceType);

            uint typeIndex = TypeMetadataMapper.GetTypeIndex(sourceType);
            ulong typeHashValue = TypeMetadataMapper.GetTypeHashValue(sourceType);

            WriteLine();

            WriteLine("return hashValue;");
            IndentationLevel--;
            WriteLine("}");
            WriteLine();

            string dispatchTableBaseIndexVariable =
                "global::" +
                (string.IsNullOrEmpty(DispatchTableCSharpNamespace) ? string.Empty : $"{DispatchTableCSharpNamespace}.")
                + "ObjectDeserializeHandler.DispatchTableBaseIndex";

            WriteBlock($@"
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                uint global::Mlos.Core.ICodegenKey.CodegenTypeIndex() => {typeIndex} + {dispatchTableBaseIndexVariable};");

            WriteBlock($@"
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                ulong global::Mlos.Core.ICodegenKey.CodegenTypeHash() => 0x{typeHashValue:x};");

            WriteBlock($@"
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                ulong global::Mlos.Core.ICodegenType.CodegenTypeSize() => {cppType.TypeSize};");

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
