# Azure Services

## Authentication

The [`AzureAuthService`](./azure_auth.py) allows us to generate tokens for authenticating with other Azure services.

The goal is to be able to support long running experiments ideally without needing prompt the user to refresh their login session to avoid timeouts.
It supports authenticating as the following identities:

### User

As a user, the only requirement is that a user is logged in via the Azure CLI before `mlos_bench` is started
(i.e., `az login` or `az login --device-login`).
This method is simpler to get started, but the drawback is that security policies might limit the period in which we can generate access tokens under a user logged in via the CLI.
This would lead to early termination of an experiment once tokens cannot be generated anymore without another interactive login by the user.

To avoid this issue, we also support automated authentication as a Service Principle, described next.

### Service Principal (SP)

Similar to above, it also requires a user to be logged in first the Azure CLI to kick off the flow for the SP.
However, this method addresses the drawback above to some extent as the since we can configure the system to automatically reauthenticate as the SP on demand and restrict its access to fewer resources to mitigate security concerns so that experiments can run as long as necessary.

The requirements of this method are:

- User logged in to Azure CLI
- An existing SP with appropriate access to the target resource group (e.g., `Contributor` role).
  > See [scripts/azure/setup-rg/README.md](../../../../../scripts/azure/setup-rg/README.md) for details on setting up the SP.
- Key vault for storing certificate.
- A certificate associated with the SP, which is stored in the key vault.
- User has access to read the necessary secrets/certificates from the key vault (e.g., `Key Vault Administrator` role).

Once the SP is setup, the flow of authentication within `mlos_bench` is as follows:

1. On initialization, retrieve the SP's certificate from the key vault as the current user and keep it in memory.
2. Log in as the SP using the certificate retrieved from the key vault.
3. During runtime when tokens are requested, we request them as the SP, reauthenticating as necessary using the certificate which is stored only in memory.

In the associated JSON config, these requirements translate into providing the following parameters:

- `spClientId` and `tenant`: The client id of the SP and the id of the tenant to which it belongs to.
- `keyVaultName`: The name of the key vault in which the SP's certificate is stored in.
- `certName`: The name under which the SP's certificate is stored in the keyvault.
