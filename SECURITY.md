# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| SDK 1.x (latest) | Yes |
| SDK 0.x (pre-release) | No |

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues directly and privately to: **security@zhilicon.ai**

Include the following in your report:

- A clear description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept code is welcome if safe to share)
- SDK version, Python version, and OS/hardware environment
- Your assessment of severity (critical / high / medium / low)
- Whether you believe the issue is already being exploited

We treat all reports as confidential and will not share your identity without your permission.

---

## Response Timeline

| Stage | Target |
|-------|--------|
| Acknowledgement | Within 2 business days |
| Initial triage and severity assessment | Within 5 business days |
| Fix or mitigation plan communicated | Within 10 business days |
| Patch release (critical/high) | Coordinated with reporter, target within 30 days |
| Public disclosure | Coordinated with reporter after fix is available |

---

## CVE Process

Zhilicon coordinates CVE assignment through MITRE for confirmed vulnerabilities in the SDK. Once a fix is available and the coordinated disclosure window has passed, we will:

1. Request a CVE number if the issue meets the threshold.
2. Publish a security advisory on this GitHub repository.
3. Update the changelog with a reference to the CVE.
4. Credit the reporter in the advisory (unless they prefer to remain anonymous).

---

## Scope

### In Scope

- The Zhilicon SDK (Python and C++ packages, `zhilicon-sdk` and `zhilicon-sdk[simulator]`)
- Code and scripts in this repository (`zhilicon-sdk-examples`)
- The developer portal at [developers.zhilicon.ai](https://developers.zhilicon.ai)
- The Zhilicon PyPI index at `pypi.zhilicon.ai`

### Out of Scope

- Third-party dependencies (report to their respective maintainers; we will track upstream fixes)
- Model weights and datasets referenced in examples (not distributed here)
- Hardware security issues in ZHI-1 silicon — report those separately to security@zhilicon.ai with subject line `HARDWARE:`
- Denial-of-service attacks that require authenticated access to internal systems

---

## Safe Harbor

Zhilicon will not pursue legal action against security researchers who:

- Report vulnerabilities in good faith following this policy
- Avoid accessing, modifying, or destroying data beyond what is necessary to demonstrate the issue
- Do not disclose the vulnerability publicly before a fix is available (coordinated disclosure)
- Do not use the vulnerability for personal gain

We consider responsible disclosure a service to the community and the industry.

---

## Security Researcher Hall of Fame

We publicly thank researchers who have helped improve Zhilicon security through responsible disclosure.

| Researcher | Contribution |
|-----------|-------------|
| *(Your name could be here — see above for how to report)* | — |

---

## Contact

Security email: **security@zhilicon.ai**

For non-security bugs, use [GitHub Issues](https://github.com/zhilicon-ai/zhilicon-sdk-examples/issues).
