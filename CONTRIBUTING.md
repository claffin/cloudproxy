# Contributing to CloudProxy

Thank you for your interest in contributing to CloudProxy! This document outlines the branch workflow and guidelines for contributing to this project.

## Branch Workflow

We use a specific branch workflow to ensure code quality and stability:

1. **Feature Branches**: All development work must be done on feature branches.
2. **Dev Branch**: Feature branches are merged into the `dev` branch via Pull Requests.
3. **Main Branch**: The `dev` branch is merged into `main` for releases.

```
feature-branch → dev → main
```

## Step-by-Step Contributing Guide

### 1. Create a New Feature Branch

Always create a new branch from the latest `dev` branch:

```bash
# Make sure you have the latest dev branch
git checkout dev
git pull origin dev

# Create and checkout a new feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Develop and test your changes on your feature branch:

```bash
# Make changes to files
# ...

# Run tests to ensure your changes don't break anything
pytest

# Commit your changes
git add .
git commit -m "Description of your changes"

# Push your branch to GitHub
git push origin feature/your-feature-name
```

### 3. Create a Pull Request to the Dev Branch

When your feature is complete:

1. Go to the GitHub repository
2. Click "Pull requests" and then "New pull request"
3. Set the base branch to `dev` and the compare branch to your feature branch
4. Click "Create pull request"
5. Add a descriptive title and description
6. Submit the PR

### 4. Code Review and Merge

- Your PR will trigger automated tests
- All tests must pass before the PR can be merged
- Other developers can review your code and suggest changes
- Once approved and tests pass, your PR will be merged into the `dev` branch

### 5. Release Process

When the `dev` branch is ready for release:

1. Create a PR from `dev` to `main`
2. This PR will be reviewed for release readiness
3. After approval and merge, the code will be automatically:
   - Tagged with a new version
   - Built and released as a Docker image
   - Published as a GitHub release

## Workflow Enforcement

This workflow is enforced by GitHub actions that:

1. Prevent direct pushes to `main` and `dev` branches
2. Run tests on all PRs to `dev` and `main`
3. Ensure PRs to `main` only come from the `dev` branch
4. Require all tests to pass before PRs can be merged
5. Automatically create releases when `dev` is merged to `main`

## Testing Guidelines

Please follow these guidelines for testing:

1. Write tests for any new features or bug fixes
2. Run the test suite locally before submitting PRs: `pytest`
3. All tests MUST pass before a PR can be merged - this is enforced by branch protection rules
4. For complex changes, consider adding new test cases to cover your changes

### Running Tests Locally

To run tests locally:

```bash
# Install test dependencies
pip install pytest pytest-mock pytest-cov

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=./ --cov-report=term
```

Thank you for following these guidelines and helping make CloudProxy better! 