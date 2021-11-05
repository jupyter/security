# Security Subcommittee for Numfocus





We ask NumFOCUS board for the creation of a security subcommittee.




The subcommittee members are not expected to have technical knowledge of the
NumFOCUS subprojects, though would they have sufficient expertise they may
decide to reply to a report/question and not forward to a subprojects. For
example reports of missing "X-Frame-Options" for static websites from automated
tools are often invalid, and do not need subproject involvements.

The subcommittee members are not expected to be proactive and act upon security
issue that are not directly reported to them.

The subcommittee is not expected to be able understand, fix, and request CVE for
issues, nor to respond to all security questions.

This subcommittee is not a replacement, nor preclude subproject having their own
security committee, work group, or contact channels for security related matter.

This subcommittee is not expected to directly work on improving security, or
defining security best practices.


We suggest the following 5 members for the initial subcommittee:

 - Volunteer 1 (affiliation, subproject if relevant), <email1@mail.com>
 - Volunteer 2 (affiliation, subproject if relevant), <email2@mail.com>
 - Volunteer 3 (affiliation, subproject if relevant), <email3@mail.com>
 - Volunteer 4 (affiliation, subproject if relevant), <email4@mail.com>
 - Volunteer 5 (affiliation, subproject if relevant), <email5@mail.com>


# Current project security process:

Many existing projects use tide lift, though this requires project maintainers
to be subscribed to tidelift – I'm not certain of all the implication.

- Numpy
- PyMC3
- Pandas
- SciPy
- Bokeh
- Dask

A few project s use custom mailing lists


- Julia : security@julialang.org.
- Matplotlib https://github.com/matplotlib/matplotlib/blob/master/SECURITY.md
  matplotlib@numfocus.org
- Jupyter / IPython (security@ipython.org)


For the following I was not able to find how to contact.

- Nteract https://github.com/nteract/nteract/security/policy
- Stan ??
- Jump ??
- Pytables ??
- Sympy ??
- FEnics ??
- Conda-Forge




---

### NumFOCUS Committee Charter - Template

The Security Committee is established under Article 5, Sections 1-2 of the NumFOCUS Bylaws.

### Purpose

Typically, NumFOCUS and all its affiliated and sponsored projects are focused on
community and strive to communicate in public.

Security in contrast often requires private communication, and timely responses,
which is at odds with the typical open-source communication channels. Setting up
specific communication channels for each subproject can be costly for projects
in term of time invested for documentation and monitoring, especially for
sub projects.

The multiple projects and different ways of inquiring about security can make it
hard for stakeholder to find how to contact the relevant projects; especially
when a question or vulnerability is related to multiple project interacting
together.


- Discussions about best practices for security in general and at a project
  level are good to have as a community and in public. People need to be
  educated and informed about security in a general sense and should be able to
  find resources they need deploy and run software securely.

- At the same time, developers need to coordinate activity in anticipation of
  and in response to software issues to do with security, in a time-sensitive
  fashion, and with discretion (it is just the reality). Each project can do
  this on its own but the structures needed are basically the same from project
  to project. In addition, I thought (restating but also expanding a bit maybe):

- Sharing structures (both infrastructure and human resources) for managing
  security across multiple projects can make it more manageable but also enable
  better propagation and awareness of issues across a set of projects that are
  often linked together or may encounter similar issues.

- A common structure may also promote a coherent approach to certain common
  security issues across projects, and forming strategies around those common
  issues actually can make running and deploying software securely easier
  ("these are NumFOCUS projects and they tend to do things this way...").

### Mission

- This subcommittee should have at least 5 members selected by the NF board.
- This subcommittee should be reachable via `security@numfocus.org`.

The following is expected from the member of this subgroup:

- to acknowledge security questions, concern or vulnerability in a short
  timeframe (maximum 1 week), and contact the relevant(s) subprojects, or
  subproject(s) maintainers.

- for a security vulnerability report: ensuring the reporter get a proper
  response. The response can be directly from the concerned subproject. The
  security subcommittee can directly provide a response if:

    - The subcommittee members have sufficient expertise to provide a response
    - The subprojects maintainers do not reply to inquiries – in which the
      matter should also be discussed with numfocus board.

- Ignore any non-security enquiries, warn and ban repeated offender from
  contacting security@numfocus.org as their discretion.
- Maintain a https://numfocus.org/security.txt text document following standard
  security practices (see https://securitytxt.org/)
- Maintain a more generic security webpage on https://numfocus.org with relevant
  information with respect to how to contact the
  subcommittee.
- Report regularly and privately to the NumFOCUS board to ensure objectives are
  reached.


### Committee Composition



1. The security committee will strive to be open to a wide range of
   contributors. In particular as it may need to coordinate communication across
   many projects, it should have representing members for many parts of the
   NumFOCUS affiliated and sponsored projects.  

2. The security committee should consist of at least 3 members with a 2 years
   term renewable at maximum once, unless approved by the NumFOCUS board.

3. General Members
    1. Responsibilities:
        1. Attend meetings as scheduled by the vice president/co-chair(s)
        2. List specific duties as applicable
        3. Assist in carrying out the committee’s objectives
    2. Elections
        1. Call for Nominations (2-4 weeks): plan for a wide and
            strategic/targeted recruitment (identify groups to notify, promotion
            channels, etc.) that includes an application to collect contact
            details and other relevant information.
        2. Members will be selected by the committee’s officers or current
        members using a rating system.
4. Officers
    1. Vice President or Chair(s)
        1. Board appointed or elected by committee members for a one-year
            term with an option to serve an additional one-year term upon
            member approval.
                1. May be submitted to the board for approval as part of a
                new committee proposal (one-year term)
        2. Responsibilities:
            1. Calls for scheduled meetings
            2. Sets the agenda for meetings
            3. Chairs the meetings according to Robert’s Rules of Order
    2. Secretary
        1. Selected by the Board of Directors or elected by committee
            members for a one-year term
        2. Responsibilities:
            1. Records all meeting minutes
            2. Submits quarterly reports to the board of directors
### Meetings

1. The committee should have written communication about the state of security at
   minimum bi-weekly.
2. W


1. The security committee meets at least monthly.
2. A majority of the committee members shall constitute a quorum.

### Committee Reports

1. Reports will be submitted to the board quarterly on or before the 15th of March, June, September, and December
2. Reports should include the following metrics:
    - Overview of activities and challenges if any
    - Budget update including spending for that quarter - if applicable



* The committee will review its charter annually and recommend any proposed changes to the board for review. If needed, the committee may update the charter before the annual review and will only be required to submit changes involving the purpose or mission to the board prior to the annual review and recommendation.


