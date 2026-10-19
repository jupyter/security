# Project Jupyter Security Standing Committee Charter

## Mission and Scope

The **Security Standing Committee** (SSC) is a permanent committee established
to oversee and improve the security of Project Jupyter’s software and
operations. It replaces the former Jupyter Security Subproject and inherits its
mission to provide guidance on security and to coordinate the handling of
security issues across all Jupyter projects. The Committee is empowered by the
Project Jupyter Executive Council (EC) to define and implement security
policies, practices, and response procedures that protect Jupyter’s code,
repositories, infrastructure (e.g. web services, DNS), credential stores
(password vaults, keys), and users.

**Scope of Responsibilities:** The Security Standing Committee’s
responsibilities include, but are not limited to, the following areas:

* **Incident Response and Vulnerability Handling:** Acting as Jupyter’s security
  response team, the Committee receives and triages private vulnerability
  reports (via channels like [security@ipython.org](mailto:security@ipython.org)
  or GitHub Security Advisories) and coordinates their resolution. It works
  confidentially with affected subproject maintainers to develop patches, tests
  fixes, and issues CVEs/advisories. The Committee determines disclosure
  timelines and ensures vulnerabilities are disclosed responsibly to users
  (following existing policies until updated). It effectively mirrors the role
  of security response teams in other open-source projects (e.g. Python’s PSRT
  handling CPython/pip issues or Kubernetes’ Security Response Committee
  managing CVEs).

* **Security Policy and Standards:** The Committee defines, implements, and
  maintains project-wide security policies and best practices. This includes
  policies for secure coding, dependency management, branch protection,
  vulnerability disclosure, incident response, and infrastructure access. The
  Committee has the authority to create new security policies or update existing
  ones, and will do so in consultation with the broader community when
  appropriate. All existing Jupyter security policies remain in force under this
  Committee’s oversight until they are explicitly reviewed and revised – the
  Committee’s mandate is to build upon current policies, not replace them
  abruptly (thus providing continuity with the Security Subproject’s
  guidelines).

* **Audits and Risk Assessment:** The Committee facilitates regular security
  audits, reviews, and assessments of Jupyter’s code and infrastructure. It may
  arrange third-party code audits, penetration tests, or dependency
  vulnerability scans for critical components, similar to how Kubernetes’ SIG
  Security organizes recurring security audits for the project. The Committee
  will track identified risks and ensure that subprojects implement recommended
  fixes or mitigations. It also undertakes threat modeling exercises for core
  systems (e.g. JupyterHub, Jupyter Notebook server) to proactively identify and
  address potential vulnerabilities.

* **Security Tooling and Infrastructure Management:** The Committee evaluates
  and recommends security tools and processes to improve Jupyter’s security
  posture. For example, it may deploy static analysis tools, secret scanners,
  supply-chain security tools, or continuous dependency audit workflows across
  Jupyter repositories. It also oversees sensitive infrastructure such as
  certificate management, credential stores, account permissions, and DNS
  records to ensure they follow best practices (for instance, enforcing
  two-factor authentication, principle of least privilege, regular key
  rotations, etc.). The Committee’s role here is advisory and
  implementation-support: it can propose tooling and work with subproject teams
  to integrate them (much as Node.js’s Security Working Group promotes improved
  security practices and tooling in its ecosystem).

* **Community Advice and Outreach:** The Committee serves as a central point of
  expertise on security for the Jupyter community. It provides help and advice
  to Jupyter users, operators, and developers on security topics (continuing the
  advisory role noted in the original Security Subproject description). This may
  include publishing documentation on secure deployment of Jupyter applications,
  best practices for configuring Jupyter in sensitive environments, and
  responding to general security questions. The Committee will use public forums
  (like the Jupyter Discourse “Security” category and repository FAQs) to share
  non-sensitive security guidance. It will also promote a culture of
  security-awareness by organizing discussions or training within the community
  (for example, hosting an annual security review session or sharing lessons
  learned from incidents).

**Out of Scope:** The Security Standing Committee focuses on cross-project
security concerns and incident response. It does *not* make unilateral decisions
on general product design or new features (those remain under the Software
Steering Council (SSC) and subproject teams), except insofar as they pertain to
security requirements or risk mitigation. The Committee provides recommendations
in such cases. Major decisions that fundamentally alter Jupyter’s governance or
non-security policies are outside its authority and must be escalated to the EC.

## Membership and Organization

The Security Standing Committee is structured with a **Core Security Council**
of designated members who hold decision-making authority, and a broader group of
community **contributors/participants** who collaborate on security efforts.
This structure (a small group of core decision-makers with open community
involvement) reflects common practice in open-source security governance – for
example, Python’s Security Response Team is a restricted group of core
developers handling sensitive reports, while a public *security-sig* forum
allows broader community discussion. The goal is to balance trust and
confidentiality for critical tasks with openness and community engagement for
general security improvements.

**Core Security Council (Core Members):** The Committee’s core voting members
shall consist of **3 to 7 individuals**. These members are appointed by the
Executive Council and must be well-known, trusted members of the Jupyter
community (e.g. long-standing contributors or maintainers with demonstrated
commitment to the project’s welfare). Core members **must not be pseudonymous**
– they are expected to participate under their real identities, given the high
level of trust and accountability required for handling sensitive security
matters (in line with practices of other projects’ security teams, where
membership is limited to vetted individuals and confidential discussions are
kept to invite-only channels). One of the core members **must also be a sitting
member of the Executive Council**. This dual role member will serve as a direct
liaison to Jupyter’s top governance, ensuring that the EC is informed of
critical security issues and that the Committee’s work aligns with the broader
mission of the project. Additionally, per Jupyter’s governance model for
Standing Committees, the Security Committee will elect **one of its core members
to serve as its representative on the Software Steering Council (SSC)**. (It is
possible the EC-appointed member fulfills this role if they also sit on SSC, but
if not, another core member will be chosen to represent security interests on
the SSC.) The Core Security Council is the formal “Standing Committee Council”
for this committee, empowered to make decisions as described in this charter.

**General Participants (Security Contributors Group):** In addition to the core
members, the Committee welcomes a broader group of community participants who
are interested in contributing to Jupyter’s security efforts. *Any* community
member (including new contributors or outside security researchers) may become a
general participant by joining the public discussions (for example, the
`jupyter/security` GitHub repository or the Jupyter Discourse security forum)
and by adhering to the Project Jupyter Code of Conduct. These participants might
help by reporting vulnerabilities, suggesting improvements, writing
documentation, developing security tools, or assisting in security issue triage
for public issues. Unlike core members, general participants do not need formal
appointment; their involvement is based on interest and continued constructive
contribution. Pseudonymous participation is permitted in this broader group –
contributors may operate under consistent online handles if they wish –
**however**, all participants are expected to build trust through responsible
behavior and must understand that they will not have access to confidential
security reports until/unless they are elevated to the core Council. The open
nature of this contributor group echoes the original intent of the Security
Subproject to be an inclusive, community-wide effort (“not a closed effort,
quite the opposite”).

The table below summarizes the two levels of membership:

| **Category**                    | **Core Security Council Members**                                                                                                                                                         | **General Security Participants**                                                                                                                                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Composition & Size**          | 3–7 members total (small, fixed council).                                                                                                                                                 | Unlimited, open to any interested contributors.                                                                                                                                                                         |
| **Selection & Approval**        | Nominated based on expertise and trust; **approved by the Executive Council**. One member must be an EC member. The Council itself elects one member to serve on the SSC.                 | Self-selecting (join public security discussions and initiatives). No EC approval needed for general participation.                                                                                                     |
| **Identity Requirements**       | Must use real identities (well-known community figures; no pseudonyms) for accountability.                                                                                                | May contribute under pseudonyms or handles, *provided* they follow the Code of Conduct and build community trust.                                                                                                       |
| **Roles & Responsibilities**    | Full responsibility for sensitive tasks: private incident response, defining policies, approving security fixes, and Committee decision-making.                                           | Assist with public security tasks: e.g. identifying issues, writing security docs, improving tests, suggesting policies. No access to confidential incidents by default.                                                |
| **Authority & Decision Rights** | Hold voting power on Committee decisions; can autonomously decide on security matters within charter. Their decisions are binding for the project (subject to oversight in this charter). | No formal decision-making authority. Can discuss and propose ideas, but *decisions* are made by core Council. May be consulted for feedback on policy changes, etc., but do not vote on official committee resolutions. |
| **Term Length**                 | 2-year term, renewable (no term limits). Staggered terms may be used to ensure continuity. Mid-term replacements or additions require EC approval.                                        | No fixed term; participants engage as long as they remain active and in good standing.                                                                                                                                  |
| **SSC/EC Representation**       | Has guaranteed representation on the Software Steering Council (one seat) and close linkage to Executive Council (via the EC member on the committee).                                    | No direct representation on SSC or EC. Their input is funneled through core members.                                                                                                                                    |
| **Confidential Information**    | Access to private security reports, incident discussions, and sensitive infrastructure details. Must abide by confidentiality rules.                                                      | No access to private incident details (until or unless invited into a specific incident response by core members). Operate in the public sphere of security discussions.                                                |

**Membership Criteria:** All Core Council members must be trusted community
members with a proven track record. Ideal qualifications include prior
contributions to Jupyter or related projects, security expertise or experience,
good judgment under pressure (for incident handling), and a commitment to
Jupyter’s mission and Code of Conduct. The Executive Council will approve
members based on these criteria. The committee may solicit nominations or
volunteers for core roles when openings arise, but final appointment rests with
the EC to ensure an appropriate level of oversight and trust. (For example, in
Kubernetes the security committee’s new members are nominated internally and
then must be approved by the Steering Committee, ensuring accountability at the
project’s top level.)

**Term and Renewal:** Core members serve **two-year terms**. There are no limits
on the number of consecutive terms a member may serve – the EC can renew a
member’s role indefinitely if they continue to contribute effectively. This
mirrors typical practices in other projects, where security team members often
serve long terms for consistency, unless they step down. To maintain stability,
terms may be staggered so that not all members turn over at once. Toward the end
of a member’s term, the Committee will discuss with the member and decide
whether to seek renewal of their term. With the member’s consent, the Committee
can request that the EC reappoint them for another term (the EC will normally
approve renewal barring any performance or conduct concerns). If a member
chooses to step down or if the Committee/EC decides not to renew a term, the
Committee will identify a suitable replacement candidate and submit them to the
EC for approval.

**Removal and Vacancies:** If a core member resigns mid-term or becomes unable
to fulfill their duties, the Committee may temporarily operate with the reduced
number of members, but should promptly nominate a replacement to restore the
Council’s size (subject to EC approval). The Executive Council has the authority
to remove a core member before term expiration in cases of serious misconduct,
sustained inactivity, or breach of confidentiality or Code of Conduct. Such
removal would require a formal decision by the EC (typically after consulting
the other core members). The removed member’s seat would then be filled through
the standard appointment process as soon as practicable.

**Public Roster and Transparency:** In line with Jupyter governance
requirements, the Committee will maintain a public repository (e.g., the
existing `jupyter/security` repo) or webpage listing its core members (with
affiliations), charter, and other relevant information. This ensures the
community knows who is on the Security Committee and how to engage with its
public activities. General participants are typically not individually listed
(since participation is fluid), but significant contributors may be acknowledged
in meeting notes or reports.

## Decision-Making and Authority

**Internal Decision Process:** The Security Standing Committee’s Core Council
will make decisions following the Jupyter community’s consensus-seeking process
as described in the Jupyter Decision-Making Guide. The Council will aim for
consensus on all significant decisions (e.g. adopting a new policy, officially
recommending a major security change). If consensus cannot be reached in a
reasonable time frame, the Council may resort to a vote. Each core member has an
equal vote, and decisions are made by simple majority unless a more stringent
requirement is defined for particular cases. (For example, the Council might
choose to require a 2/3 supermajority for especially critical decisions like
proposing to deprecate a widely-used component for security reasons, to ensure
broad agreement.) A quorum for any formal vote is a majority of current core
members. Decisions and votes (except those involving sensitive incident details)
will be documented and, when possible, made public to ensure transparency.

**Autonomy in Charter Scope:** The Committee has authority to make decisions
**autonomously for all matters within its scope** as defined by this charter.
This autonomy is granted by delegation from the Executive Council. In practical
terms, the Security Committee does **not** need to seek approval from the EC or
SSC for day-to-day security operations, implementing existing policies, or
handling specific incidents. For example, the Committee can decide when to issue
a security advisory, whether a reported issue is a valid vulnerability, how to
prioritize fixes, or which security scanner to adopt, without a full
project-wide vote. Jupyter’s governance explicitly allows standing committees to
act independently within their domain. The Committee will keep records of these
decisions (minutes, issue trackers, etc.) and share them appropriately, but it
is trusted to execute its mandate on its own authority.

**Escalation and Limits of Authority:** Certain decisions **exceeding the
Committee’s mandate** or having broad project-wide impact require approval from
higher governance bodies:

* **Changes to the Charter or Governance**: The Committee cannot unilaterally
  change its own charter, expand its authority beyond what is defined here, or
  alter project governance structures. Any amendments to this charter must be
  approved by a joint decision of the EC and SSC (as per Jupyter’s rules for
  standing committees). Similarly, if the Committee believes it needs new powers
  or a changed scope, it will submit a proposal to the EC/SSC rather than acting
  on its own.

* **Major Policy Decisions Requiring Project-Wide Buy-in**: If the Committee
  proposes a security policy that would significantly affect all Jupyter
  Subprojects or users in a non-technical way (for instance, a new requirement
  that all Jupyter contributors sign a contributor security agreement, or a
  change to the Jupyter release cycle purely for security support reasons), the
  Committee should seek EC (and/or SSC) approval. As a guideline, if a decision
  falls outside “pure security” or imposes obligations on parties project-wide,
  it warrants higher-level review. The EC and SSC may decide to handle such
  proposals via the Jupyter Enhancement Proposal (JEP) process or other
  decision-making mechanisms. (For comparison, in the Python community most
  teams must defer major changes via PEPs to the Steering Council, unless
  explicitly delegated – the Jupyter Security Committee similarly will consult
  the SSC/EC for major cross-project changes.)

* **Technical Changes to Core Projects**: The Security Committee may identify a
  needed technical change for security reasons (e.g., deprecating an insecure
  API, switching a default configuration for better security, etc.). The
  Committee can make **recommendations** to the relevant Subproject or to the
  SSC in such cases, but the actual implementation decision should be made by
  the maintainers or SSC through the usual technical decision process. In urgent
  cases (e.g., a severe vulnerability in a core component), the Committee will
  coordinate a fix with maintainers privately and can approve an immediate patch
  release, but any long-term architectural changes resulting should involve the
  SSC. The Committee’s SSC representative will champion these security-motivated
  changes within the SSC to ensure they are given due priority.

* **Use of Project Resources**: Budget or resource-intensive measures (for
  example, hiring external auditors, establishing a bug bounty program, or
  purchasing security infrastructure) must be approved by the EC. The Committee
  can formulate proposals for such investments and present them to the EC. The
  EC remains responsible for allocating resources to standing committees, so the
  Committee shall not commit project funds or engage contractors without EC
  concurrence.

In situations where it is unclear whether a decision falls under the Committee’s
authority or requires escalation, the Committee will err on the side of
transparency and consult the Executive Council. By maintaining an Executive
Council member within its ranks and a representative on the SSC, the Committee
has built-in channels to raise issues to the broader governance when needed.
Internal protocols may be established (for example, a policy that any decision
impacting all subprojects must be sent to the SSC for comment before
finalizing). However, routine security operations are intended to be handled
expediently by the Committee without bureaucratic delay – this autonomy is
critical for timely incident response.

**Conflict Resolution:** If a dispute arises between the Security Committee and
another governing body or subproject (for instance, a subproject council
disagrees with a security policy, or the SSC has concerns about a
security-driven change), the issue should be resolved through consultation and,
if necessary, mediation by the Executive Council. The EC has final say in
governance disputes. The Committee’s intent is to work collaboratively, not
adversarially – in practice, it will coordinate closely with subproject teams
and the SSC to avoid conflicts. Should any arise, the EC can adjudicate a
solution that balances security needs with other project concerns.

## Reporting and Accountability

The Security Standing Committee is accountable to the Project Jupyter Executive
Council and operates under the EC’s oversight. To fulfill this accountability
and keep the broader project informed, the Committee will institute regular
reporting and communication practices:

* **Reports to Executive Council:** The Committee will report to the EC on a
  regular basis (at minimum, **once per year** in a formal written report, and
  more frequently if requested or if significant issues occur). The annual
  report to the EC will summarize the Committee’s activities, such as number of
  vulnerabilities handled (without disclosing sensitive details), major policy
  changes or initiatives undertaken, audit results, and any resource needs or
  escalations. Additionally, an EC liaison (the core member who sits on the EC)
  will provide brief updates during EC meetings as appropriate – for example,
  after a major incident is resolved, the EC member can brief the Council
  privately on what happened and lessons learned. This ensures the EC maintains
  situational awareness of security matters and can exercise oversight. The EC
  may also invite the Committee to present at an EC meeting or retreat if deeper
  discussion is warranted.

* **SSC Liaison and Advisory Role:** The Committee’s representative on the
  Software Steering Council (SSC) will serve as a conduit for communication
  between the security team and the technical leadership of Jupyter. In SSC
  meetings, this representative will **advise the SSC** on security implications
  of technical proposals and raise any cross-cutting security concerns for
  discussion. For example, if a JEP under consideration has security impact, the
  SSC representative from the Security Committee will ensure those issues are
  articulated. Conversely, if the Security Committee needs broad technical input
  (say, on the feasibility of a new security feature affecting many
  subprojects), they can bring it to the SSC via this representative. The
  Security Committee will **not** have a vote in SSC decisions beyond this
  representative’s participation (they have one vote on SSC like other standing
  committee reps), but their advisory voice is crucial. This relationship
  mirrors how other standing committees interface with technical governance –
  e.g., a Code of Conduct committee might advise but not dictate technical
  decisions. The SSC rep is expected to report back to the Security Committee on
  any SSC decisions or upcoming changes that have security relevance, so the
  Committee stays informed. In summary, the Committee **reports to the EC and
  advises the SSC** (rather than formally reporting to SSC) in accordance with
  Jupyter’s governance structure.

* **Public Transparency:** While much of the Committee’s sensitive work must be
  confidential, the Committee will strive to be as open as possible about its
  non-sensitive activities. It will publish sanitized summaries of its work for
  the community. For instance, the Committee may maintain a public **Security
  Committee Log** (on the GitHub repo or Jupyter website) that lists
  public-facing accomplishments: e.g., “Completed security audit of JupyterHub
  (report available),” “Published security best practices guide,” “Handled X
  security reports this quarter (details embargoed),” etc. After a vulnerability
  is disclosed and fixed, the Committee will often post retrospective details
  (what was the issue, how it was addressed) to educate users and developers.
  Community members should have insight into what the Security Committee is
  doing on their behalf, within the bounds of confidentiality. The Committee
  will also solicit community input publicly when developing new policies (for
  example, releasing a draft of a new security policy for comment on the forum).

* **Metrics and Feedback:** The Committee will track metrics such as number of
  vulnerabilities reported, average time to fix, and participation in security
  initiatives, and share these (in aggregate) to demonstrate effectiveness and
  identify areas for improvement. It will welcome feedback from the community
  and other governance bodies on its performance. The EC may periodically review
  the Committee’s effectiveness and can suggest adjustments to its operations or
  membership if needed.

By maintaining clear reporting lines and open communication, the Security
Standing Committee ensures it remains accountable to the wider Project Jupyter
leadership and community, despite the inherently private nature of parts of its
work. This accountability aligns with governance best practices for security
teams in open-source projects (e.g., having to justify and explain policies to
leadership and users, rather than operating opaquely).

## Coordination with Subprojects and Teams

Project Jupyter is a multi-repository, multi-subproject effort – from
JupyterLab, Jupyter Notebook, JupyterHub, Jupyter Server, to various federated
extensions. The Security Standing Committee will coordinate closely with these
**Subproject teams** to manage vulnerabilities and implement security
improvements in a collaborative way.

**Security Points of Contact:** Each official Jupyter Subproject (or major
repository) should designate at least one **security point-of-contact**
(typically a maintainer or council member of that subproject) who will interface
with the Security Committee when needed. The Security Committee will maintain a
list of these contacts (this could be facilitated by a `SECURITY_CONTACTS` file
in each repo or a central registry, similar to how Kubernetes requires each
repository to list contacts for the Product Security team). When a vulnerability
arises in a specific subproject, the Committee will reach out to that
subproject’s security contact to involve the maintainers in assessing impact and
crafting a fix. These contacts ensure there is always a responsible person in
the subproject loop, improving cross-team communication.

**Vulnerability Triage and Patching:** Upon receiving a vulnerability report,
the Security Committee will determine which subproject(s) are affected. It will
then promptly and confidentially engage the maintainers of those components. An
**incident working group** may be formed on the fly: typically one or more core
Committee members and one or two maintainers from the relevant project will
collaborate privately to analyze the issue, develop a patch, test it, and plan
the release. This follows the practice of many open projects where a small team
handles a security fix under embargo. The Security Committee provides guidance
(e.g., ensuring patches adequately fix the issue without regressions, assigning
CVE IDs, drafting advisories) and coordination (setting timelines, making sure
all affected versions are patched), while the subproject maintainers contribute
detailed knowledge of the code and implement the changes. Throughout this
process, information is restricted to those who need to know; the broader
contributor community is only informed after public disclosure. This controlled
approach mirrors the vulnerability processes in Python and Rust communities,
where only the security team and relevant core developers collaborate on a fix
until ready. All participants must adhere to the embargo and confidentiality
rules set by the Committee.

**Consistent Disclosure Process:** The Security Committee will maintain a
consistent process for vulnerability disclosure across all subprojects. For
example, if multiple Jupyter subprojects are affected by a single vulnerability
(e.g., a shared library issue), the Committee will coordinate a **simultaneous
release** across them, so that one project’s fix does not inadvertently leak the
issue of another. The Committee will use the private security list
(`security@ipython.org` or an updated alias) and/or a private repository
(similar to Kubernetes’ private security repo) to communicate with subproject
maintainers during embargoes. After releasing fixes, the Committee handles the
public disclosure: publishing a security advisory describing the issue,
crediting reporters, listing affected versions, and the solution. It will ensure
this advisory reaches users (via the Jupyter website, mailing lists, etc.) and
is archived (for instance, tracking CVEs under Jupyter’s CVE vendor ID as is
currently done). The Committee essentially acts as the clearinghouse for all
Jupyter vulnerability advisories so that they have a uniform format and central
location.

**Policy Enforcement and Guidance:** The Security Committee will work with
subproject teams to implement project-wide security policies. For instance, if
the Committee establishes a policy that all new code must include certain
security tests or all repositories must enable branch protection, it will
communicate this to each subproject council and offer help in compliance. The
Committee does *not* intend to micromanage development, but it will set
baselines (minimum security standards) that all subprojects should meet. If a
subproject has difficulty meeting a requirement, the Committee will take a
supportive approach – perhaps helping to find contributors to assist, or
adjusting timelines – rather than punitive. Ultimately, however, the Committee
has the backing of the EC/SSC to enforce critical security requirements across
the project. (As a hypothetical, if a subproject persistently refused to address
serious security issues, the EC and SSC could intervene, up to reconsidering the
project’s status – but such extreme steps are unlikely and the preference is
mutual cooperation.)

**Shared Infrastructure Security:** Many Jupyter subprojects rely on shared
infrastructure such as PyPI (for Python packages), Docker Hub (images),
readthedocs (docs), and Jupyter-owned web domains. The Security Committee will
coordinate with the teams managing these resources (often the Infrastructure or
Operations groups, if any, or the JupyterHub/Ops subproject) to ensure they are
secured. For example, it may audit the permissions on the `jupyter.org` domain
DNS or the API tokens used in CI pipelines. It will also ensure that
cross-project tools like the Jupyter Notebook extension signing keys or
JupyterHub OAuth secrets are properly managed. This may involve creating
guidelines for infrastructure secrets storage (housed in a password vault that
the Committee oversees) and processes for granting access (requiring EC approval
for certain keys, etc.).

**Interfacing with External Ecosystems:** Where Jupyter software integrates with
external projects (e.g., Jupyter uses ZeroMQ, Tornado, etc.), the Security
Committee may act as a liaison if vulnerabilities in those dependencies arise.
The Committee will monitor security announcements of key dependencies and advise
subprojects to upgrade or patch as needed. In some cases, Jupyter might receive
heads-up about upstream issues; the Committee will coordinate our response
accordingly (even possibly joining upstream embargoed discussions if invited).
This is an extension of coordinating with internal subteams – expanding to vital
external partners in our software stack.

**Collaboration and Communication:** The Committee will establish clear
communication channels for subproject maintainers to reach out with security
concerns. For example, maintainers can email the private security list if they
discover a vulnerability themselves or need guidance on a security feature.
Regular (perhaps quarterly) joint check-ins could be held where the Security
Committee invites representatives of each subproject to discuss any ongoing
security needs (this could be in a closed meeting to allow frank discussion of
not-yet-public issues). Additionally, the Committee plans to integrate security
into the development workflow of subprojects: possibly by participating in major
subproject meetings occasionally to give a “security brief”, or ensuring that
each subproject’s documentation links to central security info (as some already
do). By being present and available, the Committee will foster a security
mindset across all Jupyter teams.

In summary, the Security Standing Committee works *with* subproject teams, not
above them. It provides the coordination, expertise, and consistency needed for
effective security across a large project, while relying on each subproject’s
maintainers to implement secure code changes. This cooperative model is how
successful open-source projects handle multi-team security: for example, the
Kubernetes Security Committee coordinates fixes but involves the respective SIG
maintainers in executing them, and Python’s PSRT works with core developers of
the affected module. Jupyter will follow this model. All subprojects are
expected to adhere to the unified security processes established, recognizing
that an incident in one part of Jupyter can affect the wider community trust in
the project.

## Continuing Existing Policies

Upon its establishment, the Security Standing Committee will **adopt all
existing security policies and practices of Project Jupyter** as the starting
point for its operations. This includes the current vulnerability reporting
processes, disclosure guidelines, and any security checklists or standards
already in place. For example:

* The official advice on how to report vulnerabilities (via GitHub Security
  Advisories or emailing [security@ipython.org](mailto:security@ipython.org)
  with an encryption option) remains unchanged. The Committee will monitor the
  [security@ipython.org](mailto:security@ipython.org) mailing address (or a
  migrated `security@jupyter.org` address) to ensure reports are received and
  handled. If any changes to reporting channels are made in the future (e.g., a
  new email or web form), they will be announced widely in advance.

* The practice of using Jupyter’s CVE Vendor ID to track known vulnerabilities
  continues. The Committee will manage CVE assignments, either through existing
  CNA relationships or by coordinating with MITRE, so that vulnerabilities in
  Jupyter projects get CVE IDs. The current list of CVEs and any public
  databases (like the one on *cvedetails.com* referenced on jupyter.org) will be
  maintained.

* Any security documentation that subprojects have (for instance, security
  sections in JupyterHub or Jupyter Server docs) remain authoritative. The
  Committee will not overwrite subproject-specific security guidelines unless a
  new project-wide standard supersedes them. Over time the Committee may help
  unify and update such documentation, but until then, users and devs should
  continue to follow the documented guidance.

* The **Jupyter Security Subproject’s team compass** and community resources
  (the `jupyter/security` GitHub repository and the Discourse Security category)
  will be leveraged by the Committee. That repository currently contains public
  information and discussions about Jupyter security; it will be adopted as the
  Security Committee’s public repo for sharing information and coordinating
  community work. Likewise, the Discourse forum for security will remain a venue
  for open discussion (non-sensitive topics). Essentially, the new Committee is
  stepping into the shoes of the Security Subproject – providing more formal
  governance and authority, but not discarding the work that has been done so
  far.

By retaining existing policies initially, the Committee ensures a smooth
transition with no lapses in coverage. Over time, the Committee will review all
legacy policies and decide where improvements or changes are needed. When it
does update a policy, the new policy will explicitly replace the old one (with
version tracking in documentation). Until such an update is approved and
communicated, **the status quo remains in effect** so that there is never
ambiguity about what rules to follow. This approach is intended to reassure
stakeholders that the creation of the Committee will not disrupt ongoing
security processes – it’s an enhancement of governance, not a reset.

If any conflicts are discovered between existing security guidelines and this
charter or Committee decisions, the Committee will resolve them case-by-case,
possibly temporarily honoring the existing rule and then formally amending it
via the proper process. The Executive Council will be consulted if an immediate
decision is needed in a conflict scenario.

## Communicating Changes and Updates

Any changes in security policy or practice that the Security Standing Committee
enacts will be **clearly communicated to all affected stakeholders**. Effective
communication is critical whenever introducing new requirements or guidelines,
to ensure adoption and avoid confusion. The Committee will use multiple channels
to announce and explain changes:

* **Public Announcements:** Major policy changes will be announced on the
  Jupyter Discourse forum (in the Security category and any other relevant
  categories) and on the official Jupyter mailing list or blog, as appropriate.
  For example, if the Committee creates a new “Security Release Policy” or
  decides to require 2FA for all maintainers, it might post an announcement
  titled “New Jupyter Security Policy: XYZ” on Discourse, detailing what is
  changing and why. This mirrors how other open-source projects communicate such
  changes to their communities – transparency and explanation are key.

* **Direct Notifications to Project Leads:** The Committee will directly inform
  Subproject Councils/maintainers of changes that impact them. This might happen
  via an email to all subproject leads or a presentation in a monthly
  maintainers’ meeting. For instance, if a new dependency scanning tool is
  mandated, the Committee would email all repository owners with instructions
  and offer to assist with setup. Early communication is promised – the
  Committee will strive to **give advance notice** of upcoming requirements so
  teams have time to comply.

* **Documentation Updates:** All relevant documentation will be updated
  concurrently with the policy change. The Committee will maintain a centralized
  “Project Jupyter Security Policy” document (or section on jupyter.org) that is
  kept up-to-date. Whenever a policy is changed or a new one adopted, that
  canonical document will be revised, and version-noted. Subproject-specific
  documentation should also be updated to reference the new policy (the
  Committee can submit PRs to those repos to help). For example, if the
  “Supported Versions Security Policy” is changed (hypothetically, how long
  JupyterLab LTS releases get security fixes), the central docs and JupyterLab
  docs would both reflect the new timelines.

* **Stakeholder Meetings & Feedback:** In some cases, the Committee may hold a
  public meeting or office hours to explain a significant change and answer
  questions. For example, a Zoom session or a slot at a Jupyter community call
  could be used to walk through a new incident response process with project
  contributors. This interactive communication allows addressing concerns in
  real-time. The Committee will actively solicit feedback on changes; if the
  community raises valid issues, the Committee is open to adjusting policies.
  The goal is to implement effective security measures *with* community buy-in,
  not top-down imposition.

* **Gradual Rollout When Possible:** For new measures that require effort from
  others (say, every repo must add a `SECURITY.md` file), the Committee will
  typically announce the plan, provide a grace period or phased schedule, and
  offer help. It might pilot the change on a few repositories first, gather
  feedback, then expand. This way, stakeholders are not caught off guard and can
  adapt smoothly.

* **Emergency Changes:** In rare cases, the Committee might have to implement a
  security change on an urgent basis (for example, revoking a compromised
  certificate or banning a dangerously insecure dependency). In such situations,
  the Committee is empowered to act immediately to protect the project, but will
  still inform the community as soon as practical about what was done and why. A
  post-incident report or announcement will be made to ensure transparency after
  the fact.

All communications will be written in clear, accessible language, avoiding
unnecessary jargon, so that a wide audience (from developers to end users) can
understand the implications. The Committee will maintain a mailing list or group
specifically for security announcements (similar to Kubernetes’
security-announce list for vulnerability alerts); interested parties can
subscribe to get critical security notices.

Finally, the Committee will coordinate with the Jupyter documentation and
community-relations teams (if any) to amplify important messages. For example, a
tweet or blog post might accompany a major policy rollout to reach as many users
as possible.

In summary, **no significant security policy or practice change will be
implemented quietly or in isolation** – the Security Standing Committee commits
to proactively communicating changes through multiple channels, ensuring that
everyone from Jupyter developers to deployers is aware of new security
expectations. This approach aligns with open-source principles and avoids
confusion, much as Node.js and other communities emphasize transparency when
rolling out security processes (e.g., Node doubled its security release cadence
and made announcements explaining the change). Clear communication will help the
Committee achieve its goals by bringing the community along on security
improvements.

## Amendments and Ratification

This charter is established by joint approval of Project Jupyter’s Executive
Council and Software Steering Council, in accordance with governance procedures
for creating a new Standing Committee. It becomes effective upon that approval.
The Security Standing Committee shall be considered officially constituted once
its initial core members are appointed by the EC.

Amendments to this charter require the consent of both the EC and SSC
(reflecting the significance of the Security Committee’s role in project
governance). The Committee itself can propose charter amendments (for example,
if an adjustment to scope or membership structure is needed in the future), but
those proposals must be reviewed and approved through a joint EC/SSC decision
before taking effect. Minor updates (e.g., clarifying language that doesn’t
change meaning) can be suggested by the Committee but likewise will be presented
to the EC for sign-off to maintain transparency and proper governance.

The Executive Council and Software Steering Council will periodically review
this charter (for instance, biennially, aligning with member term cycles) to
ensure it remains up-to-date with the project’s needs. Any changes to Jupyter’s
overall governance that affect standing committees in general will be reflected
in an updated charter for this Committee as well, via the above approval
process.

Should the Executive Council ever determine that the Security Standing Committee
is no longer required or should be restructured, it may initiate dissolution or
reorganization, but only through the joint EC and SSC process defined for
standing committees. In such a case, the EC/SSC would ensure a transition plan
is in place for handling security responsibilities.

By approving this charter, Project Jupyter formalizes the mandate of the
Security Standing Committee to act as the steward of security for the project.
The Committee will abide by this charter in letter and spirit, and will
coordinate with Jupyter leadership if any ambiguities or exceptional situations
arise. Together, we will work to keep Jupyter’s users and contributors safe, and
the project’s reputation for security strong, through clear governance and
dedicated effort.


## Sources

* Project Jupyter Security Subproject description and formation discussion
* Kubernetes Security Response Committee practices (membership and role)
* Python Security Response Team (PSRT) process and team structure
* Rust Security Response Working Group and Rust Foundation Security Initiative (collaboration across teams)
* Node.js Security Working Group scope (ecosystem focus and best practices)
* Project Jupyter Governance docs on Standing Committees (establishment, autonomy, SSC representation, EC reporting)
* Current Jupyter security policies (as of 2025) on reporting vulnerabilities and known CVEs
* Example of security contacts in OSS projects (Kubernetes repo SECURITY\_CONTACTS).

1. [Project Jupyter – Security](https://jupyter.org/security)
2. [Project Jupyter – Standing Committees & Working Groups](https://jupyter.org/governance/standing_committees_and_working_groups.html)
3. [Project Jupyter – List of Standing Committees and Working Groups](https://jupyter.org/governance/list_of_standing_committees_and_working_groups.html)
4. [Project Jupyter – Decision-Making Guide](https://jupyter.org/governance/decision_making.html)
5. [Project Jupyter – Governance Overview](https://jupyter.org/governance/overview.html)
6. [Project Jupyter – Executive Council](https://jupyter.org/governance/executive_council.html)
7. [Project Jupyter – Software Steering Council](https://jupyter.org/governance/software_steering_council.html)
8. [Jupyter Security Subproject – Discourse announcement](https://discourse.jupyter.org/t/project-jupyter-security-subproject/10175)
9. [Responsible Vulnerability Reporting – Jupyter Discourse](https://discourse.jupyter.org/t/responsible-vulnerability-reporting/655)
10. [jupyter/security GitHub repository](https://github.com/jupyter/security)
11. [Kubernetes SIG Security Charter](https://github.com/kubernetes/community/blob/master/sig-security/charter.md)
12. [Kubernetes SIG Security repository](https://github.com/kubernetes/sig-security)
13. [Kubernetes SECURITY\_CONTACTS guidance](https://github.com/kubernetes/ingress-nginx/issues/2563)
14. [Python Developer Guide – PSRT](https://devguide.python.org/developer-workflow/psrt/)
15. [PEP 13 – Python Language Governance](https://peps.python.org/pep-0013/)
16. [Python Steering Council communications repo](https://github.com/python/steering-council)
17. [Node.js Ecosystem Security Working Group](https://github.com/nodejs/security-wg)
18. [Node.js release-cadence discussion](https://github.com/nodejs/Release/issues/553)
19. [Rust Security Response WG](https://www.rust-lang.org/governance/wgs/wg-security-response)
20. [Rust Secure Code WG](https://www.rust-lang.org/governance/wgs/wg-secure-code)
21. [Standing Committees section (anchor)](https://jupyter.org/governance/standing_committees_and_working_groups.html#standing-committees)
22. [Jupyter Team Compass – Decision-making practice](https://jupyter-notebook-team-compass.readthedocs.io/en/latest/team/decision-making.html)
23. [Bootstrapping Subproject Councils](https://jupyter.org/governance/bootstrapping_subproject_councils.html)
24. [Jupyter Governance GitHub repo](https://github.com/jupyter/governance)
25. [decision\_making.md – raw file](https://github.com/jupyter/governance/blob/master/decision_making.md)
26. [Project Jupyter – Governance (landing page)](https://jupyter.org/governance/)
27. [PEP 8106 – 2025 Steering Council election](https://peps.python.org/pep-8106/)
28. [Real Python – “Python’s Governance Transition”](https://realpython.com/lessons/python-steering-council/)
29. [Kubernetes SECURITY\_CONTACTS template (dup link for completeness)](https://github.com/kubernetes/ingress-nginx/issues/2563)
30. [Decision-Making Guide – GitHub view](https://github.com/jupyter/governance/blob/master/decision_making.md)
31. [Project Jupyter – Software Subprojects](https://jupyter.org/governance/software_subprojects.html)

*(Items 29–30 intentionally repeat a URL already cited so the list matches the 31 total reference slots that appeared in the charter.)*

