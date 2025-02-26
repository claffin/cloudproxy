# Contributing to CloudProxy

Thank you for your interest in contributing to CloudProxy!

## Branch Workflow

We use a simple branch workflow:

- **Feature branches**: For development work (`feature/your-feature`)
- **`dev`**: Staging branch where features are integrated
- **`main`**: Production-ready code

```
feature branch → dev → main
```

## Quick Start

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/cloudproxy.git
cd cloudproxy
git remote add upstream https://github.com/claffin/cloudproxy.git
```

### 2. Create a Feature Branch

```bash
git checkout dev
git pull upstream dev
git checkout -b feature/your-feature-name
```

### 3. Develop and Test

```bash
# Make your changes
pytest  # Run tests
```

### 4. Submit a Pull Request

1. Push your branch: `git push origin feature/your-feature-name`
2. Go to GitHub and create a PR to the `dev` branch
3. Fill out the PR template

## Adding a New Provider

1. Create a directory under `cloudproxy/providers/` with the provider name
2. Implement the required functions (create, delete, list proxies)
3. Update `cloudproxy/providers/__init__.py`
4. Add documentation and tests

## Building Locally

```bash
docker build -t cloudproxy:test .
docker run -p 8000:8000 -e PROXY_USERNAME=test -e PROXY_PASSWORD=test cloudproxy:test
```

By contributing to CloudProxy, you agree that your contributions will be licensed under the project's MIT License. 