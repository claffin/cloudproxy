# CloudProxy UI Testing Guide

## Overview

The CloudProxy UI includes comprehensive testing coverage with both unit tests and end-to-end tests.

## Test Structure

```
tests/
├── unit/                   # Unit tests
│   ├── App.spec.js        # App component tests
│   ├── ListProxies.spec.js # Proxy management tests
│   └── RollingConfig.spec.js # Rolling deployment tests
├── mocks/                  # API mocking
│   ├── handlers.js        # MSW request handlers
│   └── server.js          # MSW server setup
└── setup.js               # Global test setup

cypress/
├── e2e/                   # End-to-end tests
│   ├── proxy-management.cy.js
│   └── rolling-deployment.cy.js
└── support/               # Cypress helpers
    ├── commands.js        # Custom commands
    └── e2e.js            # E2E configuration
```

## Running Tests

### Unit Tests (Vitest)

```bash
# Run all unit tests
npm test

# Run tests in watch mode
npm run test

# Run tests once (CI mode)
npm run test:run

# Run with coverage report
npm run test:coverage

# Open Vitest UI
npm run test:ui
```

### E2E Tests (Cypress)

```bash
# Open Cypress interactive mode
npm run cypress:open

# Run Cypress tests headlessly
npm run cypress:run

# Run E2E tests (alias for headless)
npm run test:e2e
```

### Run All Tests

```bash
# Run both unit and E2E tests
npm run test:all
```

## Test Coverage

### Unit Tests Coverage

- **App.vue**: Layout, navigation, component rendering
- **ListProxies.vue**: 
  - Provider display and sorting
  - Proxy management (add/remove)
  - Scaling controls
  - Copy to clipboard
  - Rolling deployment status
  - Auto-refresh functionality
- **RollingConfig.vue**:
  - Configuration display
  - Enable/disable toggle
  - Input validation
  - API interactions

### E2E Tests Coverage

- **Proxy Management**:
  - Full proxy lifecycle
  - Scaling operations
  - Error handling
  - Auto-refresh
- **Rolling Deployment**:
  - Configuration updates
  - Validation
  - UI interactions

## API Mocking

Tests use MSW (Mock Service Worker) for API mocking with predefined responses:

- `/providers` - Provider and proxy list
- `/rolling` - Rolling deployment configuration
- `/auth` - Authentication settings
- `/destroy` - Proxy removal queue

## Writing New Tests

### Unit Test Example

```javascript
import { mount } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import MyComponent from '@/components/MyComponent.vue';

describe('MyComponent', () => {
  it('renders correctly', () => {
    const wrapper = mount(MyComponent);
    expect(wrapper.find('.my-class').exists()).toBe(true);
  });
});
```

### E2E Test Example

```javascript
describe('My Feature', () => {
  it('performs user action', () => {
    cy.visit('/');
    cy.get('#my-button').click();
    cy.get('.result').should('contain', 'Success');
  });
});
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# GitHub Actions example
- name: Run Unit Tests
  run: npm run test:run

- name: Run E2E Tests
  run: |
    npm run serve &
    npx wait-on http://localhost:8080
    npm run test:e2e
```

## Debugging Tests

### Unit Tests
- Use `console.log()` in tests
- Use `wrapper.html()` to see component output
- Run with `--reporter=verbose` for detailed output

### E2E Tests
- Use `cy.debug()` or `cy.pause()` in tests
- Screenshots saved on failure in `cypress/screenshots/`
- Use Cypress interactive mode for step-by-step debugging

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mock Data**: Use consistent mock data across tests
3. **Async Handling**: Always wait for async operations
4. **Cleanup**: Clean up after each test
5. **Descriptive Names**: Use clear test descriptions
6. **Coverage**: Aim for >80% code coverage