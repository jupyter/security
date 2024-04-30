### Security Manager Role FAQ

- What permissions does a security manager have?
	- As per the [Github documentation](https://docs.github.com/en/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization)the security manager role has:
		- Read access on all repositories in the organization, in addition to any existing repository access
		- Write access on all security alerts in the organization
		- The ability to configure code security settings at the organization level
		- The ability to configure code security settings at the repository level
	- Someone in the `security manager` team role cannot manage the security team members

- How can the security manager permission be granted?
	- An organization owner can create and manage a `security-managers` team.
	- See [how to create a Github team](https://docs.github.com/en/organizations/organizing-members-into-teams/creating-a-team)

- Who should have the Security Manager role?
	- Trusted members of the security-council team who may be required to audit security across various Jupyter subprojects.

- What does the Security Manager role accomplish? 
	- The security manager role will give trusted members of the Jupyter Security council the permissions necessary so that they may collaborate with Jupyter sub-project maintainers in evaluating, processing and handling security across Jupyter.
	- This role may also promote a more uniform and united handling of security across the Jupyter ecosystem.  

- Who is the role accountable to and what authority does the role have over the project?
	- Security managers act in the interest of the community, ensuring security across the Jupyter ecosystem. The role offers no additional authority over the project and is intended to facilitate working with project maintainers to promote security and security best practices.

- How will `jupyter/security` stay on top of memberships of those lists?
	- The Jupyter Security council will establish an auditing schedule to ensure that the security manager team members are consistent across organizations and reflect the most current membership status for all individuals of the security manager team. 
	- The selection of the members of the `security manager team` will be an agreed upon group of members from the Jupyter Security council selected via voting in a private Jupyter organization repository. The list of members will be shared with an organization owner and any necessary changes will be communicated. 

- Does the subproject team take on any new responsibilities here?
	- No additional responsibilities are taken on by the subproject team. The Jupyter Security council will establish an auditing schedule and communicate with teams and organization owners to ensure that the security manager roles across Jupyter organizations are up to date.

- How do you imagine the role interacting with the Jupyter subproject teams in general?
	- This role should collaborate with Jupyter subproject maintainers to ensure the overall security across Jupyter subprojects.