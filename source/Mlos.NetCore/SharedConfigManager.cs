// -----------------------------------------------------------------------
// <copyright file="SharedConfigManager.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;

using Proxy.Mlos.Core.Internal;

using MlosProxyInternal = Proxy.Mlos.Core.Internal;
using ProbingPolicy = Mlos.Core.Collections.TLinearProbing<Mlos.Core.Collections.FNVHash<uint>>;

namespace Mlos.Core
{
    /// <summary>
    /// Shared config manager.
    /// </summary>
    /// <remarks>
    /// Config structures are stored in the shared memory.
    /// </remarks>
    public class SharedConfigManager : ISharedConfigAccessor
    {
        public void SetMemoryRegion(MlosProxyInternal.SharedConfigMemoryRegion sharedConfigMemoryRegion)
        {
            this.sharedConfigMemoryRegion = sharedConfigMemoryRegion;
        }

        /// <inheritdoc/>
        public SharedConfig<TProxy> Lookup<TType, TKey, TProxy>(ICodegenKey<TType, TKey, TProxy> codegenKey)
            where TType : ICodegenType, new()
            where TKey : ICodegenKey, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;
            return sharedConfigMemoryRegion.Get<ProbingPolicy, TProxy>(codegenKey, ref slotIndex);
        }

        /// <inheritdoc/>
        public SharedConfig<TProxy> Lookup<TType, TProxy>(ICodegenType<TType, TProxy> codegenType)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;
            return sharedConfigMemoryRegion.Get<ProbingPolicy, TProxy>(codegenType, ref slotIndex);
        }

        /// <inheritdoc/>
        public SharedConfig<TProxy> Lookup<TProxy>()
            where TProxy : ICodegenProxy, new()
        {
            // #TODO make sure, ICodegenProxy does not have any fields to compare
            //
            uint slotIndex = 0;
            return sharedConfigMemoryRegion.Get<ProbingPolicy, TProxy>(default(TProxy), ref slotIndex);
        }

        /// <summary>
        /// Insert element.
        /// </summary>
        /// <typeparam name="TType">Codegen configuration type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy.</typeparam>
        /// <param name="componentConfig"></param>
        public void UpdateConfig<TType, TProxy>(ComponentConfig<TType, TProxy> componentConfig)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            uint slotIndex = 0;

            SharedConfig<TProxy> sharedConfig = sharedConfigMemoryRegion.Get<ProbingPolicy, TProxy>(componentConfig.Config, ref slotIndex);

            if (sharedConfig.Buffer == IntPtr.Zero)
            {
                throw new KeyNotFoundException("Unable to locate config");
            }

            componentConfig.Config.Update(sharedConfig.Config);
        }

        /// <summary>
        /// Insert element.
        /// </summary>
        /// <typeparam name="TType">Codegen configuration type.</typeparam>
        /// <typeparam name="TProxy">Codegen proxy.</typeparam>
        /// <param name="componentConfig"></param>
        internal void Insert<TType, TProxy>(ComponentConfig<TType, TProxy> componentConfig)
            where TType : ICodegenType, new()
            where TProxy : ICodegenProxy<TType, TProxy>, new()
        {
            sharedConfigMemoryRegion.Add<ProbingPolicy, TType, TProxy>(componentConfig);
        }

        private MlosProxyInternal.SharedConfigMemoryRegion sharedConfigMemoryRegion;
    }
}