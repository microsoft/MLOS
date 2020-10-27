// -----------------------------------------------------------------------
// <copyright file="CppObjectCodeWriter.cs" company="Microsoft Corporation">
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
    /// Code writer class which generates a regular Cpp structures.
    /// </summary>
    internal class CppObjectCodeWriter : CppCodeWriter
    {
        /// <summary>
        /// Only interested in struct type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void WriteBeginFile()
        {
            WriteLine("#ifdef _MSC_VER");
            WriteLine("#pragma warning(disable : 4324) // alignas operator");
            WriteLine("#endif");
            WriteLine();
            WriteBlock(@"
                /// Structures.
                ///");
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            WriteLine("#ifdef _MSC_VER");
            WriteLine("#pragma warning(default:4324) // restore alignas operator warning");
            WriteLine("#endif");
            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            string cppClassName = sourceType.Name;
            string cppProxyTypeFullName = CppTypeMapper.GetCppProxyFullTypeName(sourceType);

            AlignAttribute alignmentAttribute = sourceType.GetCustomAttribute<AlignAttribute>();
            string structAlignAsCodeString = alignmentAttribute == null
                ? " "
                : $"alignas({alignmentAttribute.Size})";

            WriteBlock($@"
                    struct {structAlignAsCodeString}{cppClassName}
                    {{
                        typedef {cppProxyTypeFullName} ProxyObjectType;");

            IndentationLevel++;
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            CppType cppType = CppTypeMapper.GetCppType(sourceType);

            if (cppType.PaddingSize != 0)
            {
                // Include padding to match defined structure size.
                //
                WriteLine($"byte __finalPadding[{cppType.PaddingSize}];");
            }

            base.EndVisitType(sourceType);
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            AlignAttribute alignmentAttribute = cppField.FieldInfo.GetCustomAttribute<AlignAttribute>();
            string fieldCodeString = alignmentAttribute == null
                ? string.Empty
                : $"alignas({alignmentAttribute.Size}) ";

            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // Field is a fixed size array.
                //
                string cppElementTypeFullName = CppTypeMapper.GetCppFullTypeName(cppField.FieldInfo.FieldType.GetElementType());

                FixedSizeArrayAttribute arrayAttribute = cppField.FieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();

                fieldCodeString += $"std::array<{cppElementTypeFullName}, {arrayAttribute.Length}> {cppField.FieldInfo.Name} = {{ }};";
            }
            else
            {
                string cppTypeFullName = CppTypeMapper.GetCppFullTypeName(cppField.FieldInfo.FieldType);
                fieldCodeString += $"{cppTypeFullName} {cppField.FieldInfo.Name};";
            }

            WriteLine(fieldCodeString);
            WriteLine();
        }
    }
}
