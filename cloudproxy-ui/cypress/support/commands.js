// ***********************************************
// Custom commands for CloudProxy UI testing
// ***********************************************

// Command to mock API responses
Cypress.Commands.add('mockAPI', () => {
  // Mock providers endpoint
  cy.intercept('GET', '/providers', {
    statusCode: 200,
    body: {
      providers: {
        digitalocean: {
          instances: {
            default: {
              enabled: true,
              display_name: 'DigitalOcean Main',
              ips: ['192.168.1.1', '192.168.1.2'],
              scaling: { min_scaling: 2, max_scaling: 2 },
              region: 'nyc1'
            }
          }
        },
        aws: {
          instances: {
            default: {
              enabled: true,
              display_name: 'AWS',
              ips: ['10.0.0.1'],
              scaling: { min_scaling: 1, max_scaling: 1 },
              zone: 'us-east-1'
            }
          }
        }
      }
    }
  }).as('getProviders');

  // Mock rolling config endpoint
  cy.intercept('GET', '/rolling', {
    statusCode: 200,
    body: {
      config: {
        enabled: false,
        min_available: 3,
        batch_size: 2
      },
      status: {}
    }
  }).as('getRolling');

  // Mock auth endpoint
  cy.intercept('GET', '/auth', {
    statusCode: 200,
    body: {
      username: 'admin',
      password: 'testpass',
      auth_enabled: true
    }
  }).as('getAuth');

  // Mock destroy queue endpoint
  cy.intercept('GET', '/destroy', {
    statusCode: 200,
    body: {
      proxies: []
    }
  }).as('getDestroy');
});

// Command to wait for initial page load
Cypress.Commands.add('waitForPageLoad', () => {
  cy.wait(['@getProviders', '@getRolling', '@getAuth', '@getDestroy']);
});

// Command to expand rolling config panel
Cypress.Commands.add('expandRollingConfig', () => {
  cy.get('.rolling-config-panel button.btn-link').click();
  cy.get('.card-body').should('be.visible');
});

// Command to check toast notification
Cypress.Commands.add('checkToast', (message, variant = 'success') => {
  cy.get('.toast').should('be.visible');
  cy.get('.toast-body').should('contain', message);
  if (variant === 'success') {
    cy.get('.toast').should('have.class', 'bg-success');
  } else if (variant === 'danger') {
    cy.get('.toast').should('have.class', 'bg-danger');
  }
});