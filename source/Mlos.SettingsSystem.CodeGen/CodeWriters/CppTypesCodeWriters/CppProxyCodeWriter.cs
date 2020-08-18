// -----------------------------------------------------------------------
// <copyright file="CppProxyCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppTypesCodeWriters
{
    /// <summary>
    /// Code writer class for proxy view structures.
    /// </summary>
    /// <remarks>
    /// <![CDATA[
    ///     struct Point3D : public PropertyProxy<Point3D>
    ///     {
    ///     public:
    ///         Point3D(FlatBuffer flatBuffer, uint32_t offset = 0)
    ///           :  PropertyProxy<Point3D>(flatBuffer, offset)
    ///         {}
    ///
    ///         PropertyProxy<double> x = PropertyProxy<double>(flatBuffer, 0);
    ///     }
    /// ]]>
    /// </remarks>
    internal class CppProxyCodeWriter : CppCodeWriter
    {
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
            WriteBlock(@"
                /// Proxy structures.
                ///");

            WriteOpenTypeNamespace(Constants.ProxyNamespace);
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            WriteCloseTypeNamespace(Constants.ProxyNamespace);
            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            string cppClassName = sourceType.Name;
            string cppElementTypeFullName = CppTypeMapper.GenerateCppFullTypeName(sourceType);

            WriteBlock($@"
                struct {cppClassName} : public ::Mlos::Core::PropertyProxy<{cppClassName}>
                {{
                    // Define a type to an object that we are create proxy from.
                    //
                    typedef {cppElementTypeFullName} RealObjectType;

                    // Constructor.
                    //
                    {cppClassName}(::Mlos::Core::BytePtr buffer, uint32_t offset = 0)
                     :  ::Mlos::Core::PropertyProxy<{cppClassName}>(buffer, offset)
                    {{}}");
            WriteLine();

            IndentationLevel++;
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
            string cppProxyTypeFullName = CppTypeMapper.GetCppProxyFullTypeName(fieldType);

            // Write the property, for arrays, use PropertyArrayProxy.
            //
            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // Get the fixed array length and write the property.
                //
                FixedSizeArrayAttribute arrayAttribute = cppField.FieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();
                WriteLine($"::Mlos::Core::PropertyArrayProxy<{cppProxyTypeFullName}, {arrayAttribute.Length}> {fieldName}() {{ return ::Mlos::Core::PropertyArrayProxy<{cppProxyTypeFullName}, {arrayAttribute.Length}>(buffer, {fieldOffset}); }}");
            }
            else
            {
                WriteLine($"{cppProxyTypeFullName} {fieldName}() {{ return {cppProxyTypeFullName}(buffer, {fieldOffset}); }}");
            }

            WriteLine();
        }
    }
}
