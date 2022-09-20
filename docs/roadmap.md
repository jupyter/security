# Project Jupyter Security Roadmap

- Recommended by the [Project Jupyter Security Subproject](https://github.com/jupyter/security)
- Version: 0.1
- Time Period: January 1, 2023 through December 31, 2026
- Distribution: Public
- Authors: Security Subproject Council
- Approved by: SSC, Exectutive, etc.

## TLDR

If open-source projects such as Project Jupyter don't meet the
expectations of potentials users, especially organizations with
critical security needs (medicine, utilities, finance, goverment,
etc.), then the software from those projects will not be a viable
solution. This will also challenge vendors who redistribute and
provide support for open-source products. In the context of research,
the open-source software created through research funding will not
make its way into production use. Perhaps this is a slippery slope,
but this could become an existential risk to many of the software
projects relied on for research.

To remain a valuable and usable resource, Project Jupyer should:
- Define an action plan using the [OSSF Concise Guide for Developing More Secure Software](https://github.com/ossf/wg-best-practices-os-developers/blob/main/docs/Concise-Guide-for-Developing-More-Secure-Software.md#readme) as the basis.
- Use the [OSSF Concise Guide for Evaluating Open Source Software](https://github.com/ossf/wg-best-practices-os-developers/blob/main/docs/Concise-Guide-for-Evaluating-Open-Source-Software.md#readme) as a template or outline for communicating the overall state of security within Project Jupyter.

## Purpose

Security is critical because
- Project Jupyter and the Jupyter Community are strongly tied
- concern for the Community and all Jupyter adopters
- The risks regarding open-source are not just within the code itself,
 but also the projects
- [Nearly one in two industry pros scaled back open source use over security fears](https://www.theregister.com/2022/09/14/snakes_on_a_plan_anaconda/)
- [Anaconda 2022 State of Data Science](https://www.anaconda.com/state-of-data-science-report-2022)

Related to this, the [Open Source Security Foundation](https://openssf.org) has posted two concise guides:
- Concise Guide for Evaluating Open Source Software
- Concise Guide for Developing More Secure Software

The first is relevant for sites (like research institutions) that deploy open source software without vendor support. The second is appropriate for projects whose software starts being adopted broadly.

If there's a gap between these two activities, the open-source software created through research funding will not make its way into production use. Perhaps this is a slippery slope, but I see this as an existential risk to many of the software projects we rely on for research.

## Scope

- official Jupyter Subprojects
- direct products
  - source code
  - packages
  - services operated

## Time Period

January 1, 2023 through December 31, 2026

## Mission

### Project Jupyter Mission

Project Jupyter is a non-profit, open-source project, born out of the [IPython Project](https://ipython.org/) in 2014 as it evolved to support interactive data science and scientific computing across all programming languages. Jupyter will always be 100% open-source software, free for all to use and released under the liberal terms of the [modified BSD license](https://opensource.org/licenses/BSD-3-Clause).

### Jupyter Security Subproject Mission

Project Jupyter is committed to reducing risk in using, deploying, operating, or developing Jupyter software.

The Jupyter Security Subproject exists to provide help and advice to Jupyter users, operators, and developers on security topics and to help coordinate handling of security issues.

Establish security guidelines and requirements for Project Jupyter and its Subprojgects, while enabling the inclusivity of Project Jupyter.

Ensure that Project Jupyter is a viable choice for individuals and organizational users.

## Jupyter Security Strategy

Openly define, communicate, and adopt open-source development practices that align with the needs of of Jupyter users, operators, and vendors.

### Specific Goals

#### Do

Define an action plan using the [OSSF Concise Guide for Developing More Secure Software](https://github.com/ossf/wg-best-practices-os-developers/blob/main/docs/Concise-Guide-for-Developing-More-Secure-Software.md#readme) as the basis.

#### Engage

- Work with the other Subprojects to establish processes

#### Communicate

Use the [OSSF Concise Guide for Evaluating Open Source Software](https://github.com/ossf/wg-best-practices-os-developers/blob/main/docs/Concise-Guide-for-Evaluating-Open-Source-Software.md#readme) as a template or outline for communicating the overall state of security within Project Jupyter.

- Provide a self-assessment based the evaluation guidelines
- Point users and organizations requesting evaluation docs to the guidelines and self-assessement
- Promote OSSF Best Practices Badging
- Communicating vulnerabilities via Tidelift, GitHub and on the
  [Jupyter Security page](https://jupyter.org/security)

## Why not a JEP?
  
[Jupyter Enhancement
Proposals](https://jupyter.org/enhancement-proposals/README.html)
(JEPs) are primarily aimed at ensuring that changes within the source
code involving multiple Subprojects are discsussed and agreed to by
all stakeholders. This document is intended to drive changes to
Project Jupyter's operational and development practices. It is likely
that one or more JEPs will emerge as a result of this
roadmap. However, nothing about these goals impacts the Jupyter source
code. 

