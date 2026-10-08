Network Health Automation Suite:

A Python test framework that validates the health of web services across every network layer: DNS, CNAME/CDN routing, TCP, TLS certificates, HTTP, and SSH. It runs locally, in GitHub Actions CI/CD, and on a scheduled AWS EC2 instance, with results stored in S3 and delivered by email.

Built to answer one question quickly when something breaks: which layer failed?

What it does
#	Test case	What it validates
1	DNS Resolution	Hostname resolves to an IP, with resolution time measured
2	CNAME Chain and TTL	CDN aliasing (for example an Akamai edge hostname) and record TTLs via dnspython
3	TCP Connect	Raw connection to port 443, timed against an SLA threshold
4	HTTP Request	Status code, response-time SLA, Cache-Control, and CDN cache status (Server-Timing / X-Cache)
5	SSL Certificate Validation	Certificate validity, issuer, and days remaining before expiry
6	SSH Service Check	Logs into an EC2 instance with paramiko and verifies a service (nginx) is active

Every test is parametrized with @pytest.mark.parametrize, so one test definition runs across a list of URLs (plain sites and CDN-backed sites alike).

Architecture:
Push to main
GitHub Actions: run pytest
Log artifact, 30-dayretention
JSON report uploaded to S3
Deploy: git pull on EC2
cron on EC2: run suite
cron on EC2: fetch latestreport
Email with JSON attached

Design decision: test execution and alerting are decoupled. The pytest run only produces a JSON report and uploads it to S3. A separate script reads the newest report from S3 into memory (no second local copy) and emails it. The two jobs share nothing but the S3 bucket, so either schedule can change without touching the other.

Tech stack:

Language and test framework: Python 3.12, pytest

Networking libraries: socket, ssl, dnspython, requests, paramiko, subprocess

Cloud and delivery: AWS EC2, AWS S3 (boto3), SMTP via Gmail App Password (smtplib)

CI/CD and tooling: GitHub Actions (artifacts, encrypted secrets), cron, WSL (Ubuntu), python-dotenv

Standard library: os, json, pathlib, logging, platform, datetime

Project structure:

network-health-automation-suite/
├── .github/workflows/
│   └── tests.yml               # CI: test, artifact upload, deploy to EC2
├── utils/
│   ├── logger.py               # Shared logging setup
│   └── report.py               # Result recording helpers
├── reports/
│   ├── logs/                   # Timestamped .log files (gitignored)
│   └── results/                # Timestamped .json reports (gitignored)
├── test_health_check.py        # The six parametrized test cases
├── reports_upload_script.py    # Uploads the newest JSON report to S3
├── fetch_mail.py               # Fetches the latest report from S3 and emails it
├── pytest.ini
├── requirements.txt
├── .env.example                # Template of required environment variables
└── README.md

Getting started
1. Clone and install
bash
git clone https://github.com/<your-username>/network-health-automation-suite.git
cd network-health-automation-suite

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
2. Configure environment variables

Copy the template and fill in your own values:
bash
cp .env.example .env

Variable	Purpose
AWS_ACCESS_KEY_ID	IAM user key, scoped to one S3 bucket
AWS_SECRET_ACCESS_KEY	Matching secret
EC2_SSH_HOST	Public IP or hostname of the EC2 instance (use localhost when running on the instance itself)
EC2_KEY_PATH	Path to the .pem private key
EC2_USER	SSH username (ubuntu on Ubuntu AMIs)
EMAIL_SENDER	Gmail address used to send reports
EMAIL_APP_PASSWORD	Google App Password (not the account password)
RECIPIENT_EMAIL	Where reports are delivered

.env and *.pem are gitignored. Never commit credentials.

3. Run the tests
bash
pytest -v -s -ra
Flag	Effect
-v	Show each parametrized case by name
-s	Show log and print output live
-ra	Print a summary of all outcomes at the end

Run a single test:

bash
pytest -v -s -ra -k test_nginx_service_running
Sample report

Each run writes a structured JSON report (and a human-readable .log):

json
[
  {
    "test_name": "test_dns_resolution",
    "url": "https://www.example.com",
    "status": "passed",
    "duration_ms": 42.31,
    "timestamp": "2026-10-06T19:44:07.123456",
    "extra": { "ip": "93.184.216.34" }
  }
]

JSON is used for stored reports because it is machine-queryable across many runs. Plain .log files are used for the CI artifact because they are meant for a human debugging a single run.

CI/CD pipeline:

Defined in .github/workflows/tests.yml.

Test job (every push and pull request): installs dependencies, writes the SSH key from a secret, runs pytest, uploads logs as an artifact (30-day retention), and uploads the JSON report to S3.
Deploy job (push to main only, and only if tests pass): SSHes into EC2, runs git pull, and reinstalls dependencies.

All credentials live in GitHub Secrets and are injected as environment variables at runtime. The workflow maps each secret to the exact variable name the code reads.

Scheduled execution on EC2: Two independent cron jobs on the instance (example schedule)

crons:
# Run the health-check suite every 6 hours
0 */6 * * * cd ~/network-health-automation-suite && .venv/bin/pytest -v -s -ra >> reports/logs/cron_test_run.log 2>&1

# Email the latest S3 report once a day at 9 AM
0 9 * * * cd ~/network-health-automation-suite && .venv/bin/python fetch_mail.py >> reports/logs/cron_email.log 2>&1

Cron uses the virtualenv's own binaries by full path, because cron runs with a minimal PATH and none of the interactive shell's environment.

Security notes:
Least-privilege IAM: the uploader user can only PutObject, GetObject, and ListBucket on a single bucket.
No secrets in code or git history: credentials come from .env locally, GitHub Secrets in CI, and a .env on the server.
SSH key permissions: key files must be chmod 400 on a real Linux filesystem (for WSL, inside ~/.ssh, not under /mnt/c).
Known trade-offs (test instance only): paramiko.AutoAddPolicy() and StrictHostKeyChecking=no skip host-key verification, and the EC2 security group allows SSH from 0.0.0.0/0 so GitHub-hosted runners can connect. Acceptable for a throwaway learning instance; not for production.
Lessons built into the design
Not every observation deserves an assertion. Cache headers and CNAME records only exist on CDN-backed hosts, so those checks run only against inputs where the expectation is actually true.
Environment-driven configuration. One codebase runs unchanged on a laptop, a CI runner, and the server itself, with behaviour driven by environment variables and safe defaults.

Further Scope:
 Refactor into a class-based structure (HealthChecker, SSHServiceChecker)
 pytest-html report generation
 Trend analysis over historical S3 reports
 Containerize with Docker

Author:
Sai Swaroop K Devarmane

LinkedIn: https://www.linkedin.com/in/i-am-sai/