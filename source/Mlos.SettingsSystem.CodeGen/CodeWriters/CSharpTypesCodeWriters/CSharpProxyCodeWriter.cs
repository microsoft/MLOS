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
            string typeFullType = $"global::{sourceType.GetTypeFullName()}";
            string proxyFullName = $"{Constants.ProxyNamespace}.{sourceType.GetTypeFullName()}";

            WriteBlock($@"
                public partial struct {typeName} : ICodegenProxy<{typeFullType}, {proxyFullName}>
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
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                uint global::Mlos.Core.ICodegenKey.CodegenTypeIndex()
                {{
                    return {typeIndex} + {DispatchTableBaseIndexVariableName};
                }}");

            WriteBlock($@"
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                ulong global::Mlos.Core.ICodegenKey.CodegenTypeHash() => 0x{typeHashValue:x};");

            WriteBlock($@"
                [MethodImpl(MethodImplOptions.AggressiveInlining)]
                public ulong CodegenTypeSize() => {cppType.TypeSize};");

            WriteBlock($@"
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

            // Get the proxy type name.
            //
            string fieldTypeName = $"global::{fieldType.FullName}";

            // Write the property, for arrays, use PropertyArrayProxy.
            //
            if (cppField.FieldInfo.IsFixedSizedArray() ||
                cppField.CppType.IsCodegenType)
            {
                string csharpProxyTypeFullName = cppType.IsCodegenType ? $"global::Proxy.{fieldType.FullName}" : $"global::{fieldType.FullName}";

                if (cppField.FieldInfo.IsFixedSizedArray())
                {
                    string csharpArrayProxyTypeName = cppType.IsCodegenType ? "global::Mlos.Core.PropertyProxyArray" : "global::Mlos.Core.ProxyArray";

                    // Declare the property.
                    //
                    WriteLine($@"public {csharpArrayProxyTypeName}<{csharpProxyTypeFullName}> {fieldName} => new {csharpArrayProxyTypeName}<{csharpProxyTypeFullName}>(buffer + {fieldOffset}, {cppType.TypeSize});");
                }
                else
                {
                    WriteLine($@"public {csharpProxyTypeFullName} {fieldName} => new {csharpProxyTypeFullName}() {{ Buffer = buffer + {fieldOffset} }};");
                }
            }
            else
            {
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
