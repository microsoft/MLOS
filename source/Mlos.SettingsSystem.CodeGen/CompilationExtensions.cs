// -----------------------------------------------------------------------
// <copyright file="CompilationExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.CodeAnalysis;

namespace Mlos.SettingsSystem.CodeGen
{
    /// <summary>
    /// Extension methods for Roslyn Compiler class.
    /// </summary>
    /// <remarks>
    /// Used to locate types defintion in the source file.
    /// </remarks>
    public static class CompilationExtensions
    {
        /// <summary>
        /// Get the file line position for a given type within the compilation.
        /// </summary>
        /// <param name="compilation"></param>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        public static FileLinePositionSpan GetFileLinePosition(this Compilation compilation, Type sourceType)
        {
            INamedTypeSymbol namedTypeSymbol = compilation.GetTypeByMetadataName(sourceType.FullName);

            Location location = namedTypeSymbol.Locations.First();
            return location.GetLineSpan();
        }

        /// <summary>
        /// Get the file line position for a given field within the compilation.
        /// </summary>
        /// <param name="compilation"></param>
        /// <param name="sourcefield"></param>
        /// <returns></returns>
        public static FileLinePositionSpan GetFileLinePosition(this Compilation compilation, FieldInfo sourcefield)
        {
            INamedTypeSymbol namedTypeSymbol = compilation.GetTypeByMetadataName(sourcefield.DeclaringType.FullName);

            ISymbol symbol = namedTypeSymbol.GetMembers().First(r => r.Name == sourcefield.Name);

            Location location = symbol.Locations.First();
            return location.GetLineSpan();
        }

        /// <summary>
        /// Get the string definition of a sourceType from the compilation.
        /// </summary>
        /// <param name="compilation"></param>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        public static string GetTypeDefinition(this Compilation compilation, Type sourceType)
        {
            INamedTypeSymbol sourceTypeSymbol = compilation.GetTypeByMetadataName(sourceType.FullName);
            StringBuilder builder = new StringBuilder();

            foreach (Location location in sourceTypeSymbol.Locations)
            {
                SyntaxNode root = location.SourceTree.GetRoot();
                Location structDefLocation = root.FindToken(location.SourceSpan.Start).Parent.GetLocation();
                builder.Append(structDefLocation.SourceTree.GetText().GetSubText(structDefLocation.SourceSpan).ToString());
            }

            string structSourceCode = builder.ToString();

            // Remove whiteSpace characters
            //
            structSourceCode = Regex.Replace(structSourceCode, @"\s+", string.Empty);

            return structSourceCode;
        }
    }
}
