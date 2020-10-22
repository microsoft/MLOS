// -----------------------------------------------------------------------
// <copyright file="CppTypeReflectionTableCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Linq;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters
{
    /// <summary>
    /// Creates a table with type reflection information.
    /// </summary>
    internal class CppTypeReflectionTableCodeWriter : CppTypeTableCodeWriter
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="CppTypeReflectionTableCodeWriter"/> class.
        /// </summary>
        /// <param name="sourceTypesAssembly"></param>
        public CppTypeReflectionTableCodeWriter(Assembly sourceTypesAssembly)
            : base(sourceTypesAssembly)
        {
        }

        /// <inheritdoc />
        public override bool Accept(Type sourceType)
        {
            return sourceType.IsCodegenType();
        }

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        /// <remarks>
        /// Proxy structures are defined in namespace Proxy.
        /// </remarks>
        public override void WriteBeginFile()
        {
            WriteLine("// Cpp type reflection information.");
            WriteLine("//");

            WriteGlobalBeginNamespace();

            WriteLine("struct ReflectionTable");
            WriteLine("{");

            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            WriteLine($"uint32_t TotalClassCount = {ClassCount};");

            IndentationLevel--;
            WriteLine("};");
            WriteLine();

            WriteGlobalEndNamespace();
        }

        /// <summary>
        /// For a new structure, create a entry in matadata table.
        /// </summary>
        /// <param name="sourceType"></param>
        public override void BeginVisitType(Type sourceType)
        {
            string cppClassName = CppTypeMapper.GenerateFieldNameFromCppFullTypeName(sourceType);

            // Align name
            //
            int nameLength = (((cppClassName.Length + 1) + 7) / 8) * 8;

            // Write a link to next metadata object.
            //
            WriteLine($"uint32_t NextOffset_{cppClassName} = {metadataOffset + nameLength + sizeof(uint)};");

            // Write a class name using std::array.
            // std::array<5, char> = { 'C', 'l', 'a', 's', 's', '\0' };
            //
            WriteLine($"std::array<char, {nameLength}> TypeName_{cppClassName} =  {{ {string.Join(",", cppClassName.Select(r => $"'{r}'"))}, '\\0' }};");

            metadataOffset += nameLength + sizeof(uint);

            ++ClassCount;
        }

        private int metadataOffset = 0;

        /// <inheritdoc />
        public override string FilePostfix => "_dispatch.h";
    }
}
