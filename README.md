# UNIC Student-ran Study Material Repository

## Table of Contents

- [UNIC Student-ran Study Material Repository](#unic-student-ran-study-material-repository)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
    - [Navigation](#navigation)
  - [Repository manager](#repository-manager)
    - [Prerequisites](#prerequisites)
    - [First-time setup](#first-time-setup)
    - [Moodle sync workflow](#moodle-sync-workflow)

## Introduction

This repository serves as a collaborative resource for University of Nicosia students to share and access study materials.

### Navigation

- The repository is structured in a tree-like structure, with the root being the `Unic` folder.

   > Unic (root of the repository)
   >
     >> The course abbreviation is the course code in the format of `COURSE-###` (e.g. `MATH-101`, `COMP-101`, etc).
   >>> Unique Course Code (for example, <https://portal.unic.ac.cy/courses/355025> is `355025`)
    >>>> The course material is organized in folders: `Labs`, `Lectures`, `Books`, `Notes`, etc.
        
## Repository manager

The `mgr` directory contains a small command-line helper that keeps this folder structure tidy and can now synchronise courses directly from Moodle using an authorized web-service token.

### Prerequisites

1. Ensure Python 3.10 or newer is available on your system.
1. Install the required dependencies once:

```bash
python -m pip install -r requirements.txt
```

1. Generate a personal Moodle web-service token:
  - Log into Moodle in your browser.
  - Open **Preferences → Security keys (or Web services tokens)**.
  - Create a new token with the `Moodle mobile web service` service.
  - Copy the token; you will need it only once inside the manager.

> 💡 Tokens are tied to your account. Keep them private and revoke them if your device is lost.

### First-time setup

Run the manager from the repository root so it picks up the existing folders:

```bash
python -m mgr.mgr
```

Choose option **4. Configure Moodle credentials** and provide:

- The Moodle base URL (for UNIC this is usually `https://courses.unic.ac.cy`).
- Your personal token. It is stored in the operating system’s keyring (fallback: encrypted file in `~/.config/unic-manager/secrets.json`) so it never lands in git.
- Optionally paste the matching **private token** – this allows the manager to auto-refresh without asking for your password.
- Optionally set the username and password that should be cached for refresh if no private token is available.
- Whether downloads should fetch attached files, plus an optional file-size limit.
- A refresh interval in hours (defaults to 720 ≈ 30 days). Set it to `0` to disable automatic renewal.

The non-secret configuration remains in `~/.config/unic-manager/config.json`. You can override settings for a single run via environment variables such as `UNIC_MOODLE_TOKEN`, `UNIC_MOODLE_PRIVATETOKEN`, or `UNIC_MOODLE_BASE_URL`.

### Moodle sync workflow

After configuration, select **3. Sync courses from Moodle**. The tool will:

- Fetch your enrolments using the Moodle REST API.
- Create/refresh course directories matching `COURSE-###/<course id>`.
- Store metadata in `course.json` and `contents.json` inside each course folder.
- Optionally download attached files (respecting your size limit).

Provide a comma-separated filter if you only want specific courses (e.g. `COMP-113,355025`).

The script keeps manual actions (`Search`, `Add folder from URL`) available for quick tweaks.

### Credential storage and refresh

- Secrets (token, private token, optional password) reside in the system keyring under the service name `unic-manager`. When no keyring backend is available, they fall back to `~/.config/unic-manager/secrets.json` (chmod 600).
- `last_token_acquired` and refresh attempt timestamps are tracked in the config file to prevent silent expiry.
- The manager attempts to refresh tokens automatically when the TTL is exceeded or when Moodle returns “invalidtoken”. If refresh details are missing, you’ll be asked to reconfigure.
- To clear all stored credentials, run the configuration menu and enter `-` for the token/private token/password prompts. This removes the secrets but leaves the configuration intact.
