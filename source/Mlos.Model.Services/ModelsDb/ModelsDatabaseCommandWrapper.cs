// -----------------------------------------------------------------------
// <copyright file="ModelsDatabaseCommandWrapper.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Data.SqlClient;

namespace Mlos.Model.Services.ModelsDb
{
    /// <summary>
    /// An attempt at reducing the boilerplate at the beginning of each of ModelsDatabase methods.
    /// </summary>
    public sealed class ModelsDatabaseCommandWrapper : IDisposable
    {
        public ModelsDatabaseCommandWrapper(string connectionString)
        {
            connection = new SqlConnection(connectionString);

            connection.Open();
            Command = new SqlCommand(cmdText: null, connection: connection);
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        #region IDisposable Support

        private void Dispose(bool disposing)
        {
            if (disposed)
            {
                return;
            }

            if (disposing)
            {
                Command?.Dispose();
                Command = null;

                connection?.Dispose();
                connection = null;
            }

            disposed = true;
        }

        #endregion

        public SqlCommand Command { get; private set; }

        private SqlConnection connection;

        private bool disposed;
    }
}
