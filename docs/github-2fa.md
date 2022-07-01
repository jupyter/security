*This requirement and the outlined plan was discussed and agreed upon at the Jupyter Governance meeting on Friday, July 1, 2022.*

# Requiring 2FA for Jupyter GitHub Organizations

By October 1, 2022, Project Jupyter aims to [require two-factor authentication (2FA)](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization) for
all GitHub organizations hosting repositories for [official Jupyter Subprojects](https://jupyter.org/governance/list_of_subprojects.html#official-subprojects-with-ssc-representation).

[Enabling 2FA](https://github.blog/2021-08-16-securing-your-github-account-two-factor-authentication/) is the single most important step Jupyter contributors can take to protect their GitHub accounts from bad actors. This benefits the entire Jupyter Community by reducing the chance for malicious code to be slipped into a repository.

Fortunately, most Jupyter GitHub organization members and external collaborators have 2FA enabled, at this time. This process will get us to 100% so we can enable the requirement as a GitHub org setting.

## What's the process?

[GitHub Documentation on 2FA](https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa)

We recommend that all GitHub users secure their account with 2FA, even if you don't have an organizational role like admin or owner, or write permissions to a Jupyter repository.

Over the next month (by August 1, 2022) contributors to the Jupyter Security Subproject will reach out to owners of each Jupyter GitHub org with a list of their users without 2FA enabled. The list of users will be an intersection across the GitHub orgs so that users aren't contacted multiple times, and org maintainers are asked to do double work.

From there, the org owners can decide how they want to work within their area of the Community. They may choose to contact the users or ask the Security Subproject to reach out to the users. Or, the users without 2FA may no longer need the access or role they were granted. 

At end of August, 2022, we'll review the list of the remaining accounts without 2FA. (Hopefully none!) If possible, we'll begin enabling the requirement on our GitHub orgs. The Security Subproject will work with org owners on plans for contacting any remaining users.

At the end of September, 2022, users without 2FA enabled may lose explicit permissions or roles within Jupyter GitHub orgs. This will only impact access to private repositories, commit privileges, or having a role such as owner or admin. Read access to public repositories will remain the same, along with opening issues or pull requests. And once users enable 2FA on their account, any previous permissions or roles can be restored.

## What GitHub orgs does this apply to?

All GitHub orgs hosting repositories for [official Jupyter Subprojects](https://jupyter.org/governance/list_of_subprojects.html#official-subprojects-with-ssc-representation).

- [IPython](https://github.com/ipython/)
- [Jupyter](https://github.com/jupyter/)
- [Jupyter Lab](https://github.com/jupyterlab/)
- [JupyterHub](https://github.com/jupyterhub/)
- [Voilà](https://github.com/voila-dashboards/)
- [Jupyter Server](https://github.com/jupyter-server/)
- [Jupyter Widgets](https://github.com/jupyter-widgets/)
- [jupyter-xeus](https://github.com/jupyter-xeus/)
