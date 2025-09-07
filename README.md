# Nsynca -  Notion sync/update toolkit

- A lightweight Python toolkit for syncing, updating, and analyzing Notion databases through the official REST API.
- Provides modular updaters for:
  - **Tasks** → track project progress
  - **Deployments** → track versions and releases
  - **Services + Charges** → manage subscriptions and payments
- Creates or updates Notion pages as needed
- Includes a GUI for one-click updates, logs, and results
- Saves hours of manual work and keeps dashboards accurate and consistent
_ Stakeholders: project managers, developers, data scientists, and anyone managing multiple projects or subscriptions in Notion.

<img src="https://github.com/lisekarimi/nsynca/blob/main/assets/img/gui_update.png?raw=true" width="200"/>
<img src="https://github.com/lisekarimi/nsynca/blob/main/assets/img/gui_logs.png?raw=true" width="250"/>

## Pre-requisites

**Notion Setup:**
- Create an [integration in Notion](https://www.notion.so/profile/integrations)
- Share database access: Open database → ••• → Connections → Add your integration

**Development Tools:**
- Python 3.11.x (not 3.12+)
- [uv package manager](https://docs.astral.sh/uv/getting-started/installation/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Make: `winget install GnuWin32.Make` (Windows) | `brew install make` (macOS) | `sudo apt install make` (Linux)

## Installation Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/lisekarimi/nsynca.git
   cd nsynca
   ```

2. **Set Up Environment**:
   - Copy the `.env.example` to `.env` and fill in the required environment variables.
   - Install dependencies using `uv`:
     ```bash
     uv sync
     ```

## Usage

### Graphical User Interface

```bash
make gui
```

### Docker
```bash
make docker-build
make docker-dev
```
📌 All available commands are documented in the `Makefile`.

## 📦 Executable

Build standalone .exe:
```bash
make build-exe  # Generate spec file
make compile-exe # Create executable
```
Find executable in `dist/` folder - create desktop shortcut for daily use.

## 📑 Logs

**Log locations:**
- Development: `logs/` in project root
- Executable: `dist/logs/` next to the `.exe` file

**View logs:**
- Open the GUI to browse logs from previous runs
- Filter by month, update type, or status (success, failed)

## Development

- **Code Quality**: Use `make lint` to check code quality and `make fix` to auto-fix issues.
- **Security**: **Gitleaks** is integrated to scan for secrets in commits.
- **Pre-commit Hooks**: Install hooks using `make install-hooks`.
- **CI/CD**: Automated workflows run via **GitHub Actions** for build, linting, and testing.

## 🔐 Publishing Docker Image to GitHub Packages

The Docker image for this project is hosted in GitHub Packages.

**Prerequisites:**
1. **Generate GitHub PAT**: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Name: "Docker Package Registry"
   - Expiration: 1 year
   - Scopes: `write:packages`, `read:packages`
   - Copy the token immediately

2. **Add to .env**: Store as `GITHUB_TOKEN`

3. **Build & publish**: Use Makefile commands to build, tag, and push the image

📌 All Docker commands are available in the `Makefile`.
