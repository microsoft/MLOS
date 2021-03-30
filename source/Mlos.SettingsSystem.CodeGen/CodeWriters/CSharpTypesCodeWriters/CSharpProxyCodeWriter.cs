// -----------------------------------------------------------------------
// <copyright file="CSharpProxyCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpTypesCodeWriters
{
    /// <summary>
    /// Code writer class for CSharp proxy view structures.
    /// </summary>
    /// <remarks>
    /// Writes all properties.
    /// </remarks>
    internal class CSharpProxyCodeWriter : CSharpCodeWriter
    {
        /// <summary>
        /// Gets name of dispatch table base index variable.
        /// </summary>
        private string DispatchTableBaseIndexVariableName { get; }

        /// <summary>
        /// Initializes a new instance of the <see cref="CSharpProxyCodeWriter"/> class.
        /// </summary>
        /// <remarks>
        /// Get DispatchTable namespace from the custom assembly attribute.
        /// </remarks>
        /// <param name="sourceTypesAssembly"></param>
        public CSharpProxyCodeWriter(Assembly sourceTypesAssembly)
        {
            DispatchTableBaseIndexVariableName = sourceTypesAssembly.GetDispatchTableBaseIndexVariableName();
        }

        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            WriteLine($"namespace {Constants.ProxyNamespace}.{@namespace}");
            WriteLine("{");

            ++IndentationLevel;
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            --IndentationLevel;
            WriteLine($"}} // end namespace {Constants.ProxyNamespace}.{@namespace}");

            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType.DeclaringType);

            string typeName = sourceType.Name;
            string typeFullName = $"global::{sourceType.GetTypeFullName()}";
            string proxyTypeFullName = $"{Constants.ProxyNamespace}.{sourceType.GetTypeFullName()}";

            WriteBlock($@"
                [System.CodeDom.Compiler.GeneratedCodeAttribute(""Mlos.SettingsSystem.CodeGen"", """")]
                public partial struct {typeName} : ICodegenProxy<{typeFullName}, {proxyTypeFullName}>, IEquatable<{proxyTypeFullName}>, IEquatable<{typeFullName}>
                {{
                    public static Action<{typeName}> Callback;");

            IndentationLevel++;
            WriteLine();
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            // Get the cppType.
            //
            CppType cppType = CppTypeMapper.GetCppType(sourceType);

            uint typeIndex = TypeMetadataMapper.GetTypeIndex(sourceType);
            ulong typeHashValue = TypeMetadataMapper.GetTypeHashValue(sourceType);

            WriteBlock($@"
                /// <inheritdoc/>
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                uint global::Mlos.Core.ICodegenKey.CodegenTypeIndex()
                {{
                    return {typeIndex} + {DispatchTableBaseIndexVariableName};
                }}");

            WriteBlock($@"
                /// <inheritdoc/>
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                ulong global::Mlos.Core.ICodegenKey.CodegenTypeHash() => 0x{typeHashValue:x};");

            WriteBlock($@"
                /// <inheritdoc/>
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                public ulong CodegenTypeSize() => {cppType.TypeSize};");

            WriteBlock($@"
                /// <inheritdoc/>
                [System.Text.Json.Serialization.JsonIgnore]
                public IntPtr Buffer
                {{
                    get
                    {{
                        return buffer;
                    }}
                    set
                    {{
                        buffer = value;
                    }}
                }}");

            WriteBlock($@"
                private IntPtr buffer;");

            WriteCloseTypeDeclaration(sourceType);
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            string fieldName = cppField.FieldInfo.Name;
            string fieldOffset = $"{cppField.CppStructOffset}";

            Type fieldType = cppField.FieldInfo.FieldType;
            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // When field is array, get element type to use correct proxy type.
                //
                fieldType = fieldType.GetElementType();
            }

            // Get the proxy type name.
            //
            CppType cppType = CppTypeMapper.GetCppType(fieldType);

            // Write the property, for arrays, use PropertyArrayProxy.
            //
            if (cppField.FieldInfo.IsFixedSizedArray() ||
                cppField.CppType.IsCodegenType)
            {
                string codegenTypeFullName = $"global::{fieldType.FullName}";
                string codegenProxyTypeFullName = $"global::{Constants.ProxyNamespace}.{fieldType.FullName}";

                if (cppField.FieldInfo.IsFixedSizedArray())
                {
                    if (cppType.IsCodegenType)
                    {
                        // Declare the property.
                        //
                        WriteLine(
                            $@"public global::Mlos.Core.PropertyProxyArray<{codegenTypeFullName}, {codegenProxyTypeFullName}> {fieldName} => new global::Mlos.Core.PropertyProxyArray<{codegenTypeFullName}, {codegenProxyTypeFullName}>(buffer + {fieldOffset}, {cppType.TypeSize});");
                    }
                    else
                    {
                        // Declare the property.
                        //
                        WriteLine(
                            $@"public global::Mlos.Core.ProxyArray<{codegenTypeFullName}> {fieldName} => new global::Mlos.Core.ProxyArray<{codegenTypeFullName}>(buffer + {fieldOffset}, {cppType.TypeSize});");
                    }
                }
                else
                {
                    WriteLine($@"public {codegenProxyTypeFullName} {fieldName} => new {codegenProxyTypeFullName}() {{ Buffer = buffer + {fieldOffset} }};");
                }
            }
            else
            {
                string fieldTypeName = $"global::{fieldType.FullName}";

                WriteBlock($@"
                    public {fieldTypeName} {fieldName}
                    {{
                        get
                        {{
                            unsafe
                            {{
                                return *({fieldTypeName}*)(buffer + {fieldOffset}).ToPointer();
                            }}
                        }}

                        set
                        {{
                            unsafe
                            {{
                                *({fieldTypeName}*)(buffer + {fieldOffset}).ToPointer() = value;
                            }}
                        }}
                    }}");
            }

            WriteLine();
        }
    }
}
