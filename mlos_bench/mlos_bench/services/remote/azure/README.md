# Azure Services

## Authentication

This service allows us to generate tokens for authenticating with other Azure services.
It supports authenticating as the following identities:

### User

As a user, the only requirement is that a user is logged in via the Azure CLI before `mlos_bench` is started i.e. `az login` or `az login --device-login`.
This method is simpler to get started, but the drawback is that organization policies might limit the period in which we can generate access tokens under a user logged in via the CLI.
This would lead to early termination of an experiment once tokens cannot be generated anymore without another interactive login by the user.

### Service Principal (SP)

Similar to above, it also requires a user to be logged in first the Azure CLI to kick off the flow for the SP.
However, this method addresses the drawback above to some extent as the login for a SP can be set to expire much later i.e. when the associated certificate expires in a year.

The requirements of this method are:
- User logged in to Azure CLI
- An existing SP with appropriate access to the target resource group i.e. `Contributor` role.
- Key vault for storing certificate.
- A certificate associated with the SP, which is stored in the key vault.
- User has access to read secrets / certificates from the key vault i.e. `Key Vault Administrator` role.

The flow of authentication is as follows:
1. On initialization, retrieve the SP's certificate from the key vault as the current user.
2. Log in as the SP using the certificate
3. During runtime when tokens are requested, we request them as the SP

Although the user's login will expire earlier, it is only required on initialization.
We retain the SP's credentials in memory while `mlos_bench` is running so that no interactive logins are required until the process ends.

In the associated JSON config, these requirements translate into providing the following parameters:
- `spClientId` & `tenant`: The client id of the SP and the id of the tenant to which it belongs to.
- `keyVaultName`: The name of the key vault in which the SP's certificate is stored in.
- `certName`: The name under which the SP's certificate is stored in the keyvault.