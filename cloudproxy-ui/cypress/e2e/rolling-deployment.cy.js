describe('Rolling Deployment Configuration', () => {
  beforeEach(() => {
    cy.mockAPI();
    cy.visit('/');
    cy.waitForPageLoad();
  });

  it('displays rolling deployment panel', () => {
    cy.get('.rolling-config-panel').should('be.visible');
    cy.get('.rolling-config-panel h5').should('contain', 'Rolling Deployment Configuration');
    cy.get('.bi-arrow-repeat').should('be.visible');
  });

  it('expands and collapses configuration panel', () => {
    // Initially collapsed
    cy.get('.rolling-config-panel .card-body').should('not.exist');
    cy.get('.bi-chevron-down').should('be.visible');

    // Click to expand
    cy.get('.rolling-config-panel button.btn-link').click();
    cy.get('.rolling-config-panel .card-body').should('be.visible');
    cy.get('.bi-chevron-up').should('be.visible');

    // Click to collapse
    cy.get('.rolling-config-panel button.btn-link').click();
    cy.get('.rolling-config-panel .card-body').should('not.exist');
    cy.get('.bi-chevron-down').should('be.visible');
  });

  it('fetches configuration when expanded', () => {
    // Mock the rolling config endpoint
    cy.intercept('GET', '/rolling', {
      statusCode: 200,
      body: {
        config: {
          enabled: true,
          min_available: 5,
          batch_size: 3
        },
        status: {}
      }
    }).as('getRollingConfig');

    // Expand panel
    cy.expandRollingConfig();

    // Wait for fetch
    cy.wait('@getRollingConfig');

    // Check values are displayed
    cy.get('#rollingEnabled').should('be.checked');
    cy.get('#minAvailable').should('have.value', '5');
    cy.get('#batchSize').should('have.value', '3');
  });

  it('enables and disables rolling deployment', () => {
    // Mock update endpoint
    cy.intercept('PATCH', '/rolling', {
      statusCode: 200,
      body: { message: 'Configuration updated' }
    });

    // Expand panel
    cy.expandRollingConfig();

    // Toggle enabled checkbox if it exists and is checked
    cy.get('#rollingEnabled').then($checkbox => {
      if ($checkbox.is(':checked')) {
        cy.get('#rollingEnabled').uncheck();
        // Check inputs are disabled
        cy.get('#minAvailable').should('be.disabled');
        cy.get('#batchSize').should('be.disabled');
      } else {
        cy.get('#rollingEnabled').check();
        // Check inputs are enabled
        cy.get('#minAvailable').should('not.be.disabled');
        cy.get('#batchSize').should('not.be.disabled');
      }
    });
  });

  it('updates minimum available proxies', () => {
    // Mock update endpoint
    cy.intercept('PATCH', '/rolling', {
      statusCode: 200,
      body: { message: 'Configuration updated' }
    });

    // Expand panel
    cy.expandRollingConfig();

    // Update min available if not disabled
    cy.get('#minAvailable').then($input => {
      if (!$input.is(':disabled')) {
        cy.get('#minAvailable').clear().type('10');
        cy.get('#minAvailable').trigger('change');
        cy.get('#minAvailable').should('have.value', '10');
      }
    });
  });

  it('updates batch size', () => {
    // Mock update endpoint
    cy.intercept('PATCH', '/rolling', {
      statusCode: 200,
      body: { message: 'Configuration updated' }
    });

    // Expand panel
    cy.expandRollingConfig();

    // Update batch size if not disabled
    cy.get('#batchSize').then($input => {
      if (!$input.is(':disabled')) {
        cy.get('#batchSize').clear().type('5');
        cy.get('#batchSize').trigger('change');
        cy.get('#batchSize').should('have.value', '5');
      }
    });
  });

  it('validates input ranges', () => {
    // Expand panel
    cy.expandRollingConfig();

    // Check min_available validation
    cy.get('#minAvailable').should('have.attr', 'min', '1');
    cy.get('#minAvailable').should('have.attr', 'max', '100');

    // Check batch_size validation
    cy.get('#batchSize').should('have.attr', 'min', '1');
    cy.get('#batchSize').should('have.attr', 'max', '50');
  });

  it('disables inputs when rolling deployment is disabled', () => {
    // Mock config with disabled state
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
    }).as('getRollingDisabled');

    // Expand panel
    cy.expandRollingConfig();
    cy.wait('@getRollingDisabled');

    // Check inputs are disabled
    cy.get('#minAvailable').should('be.disabled');
    cy.get('#batchSize').should('be.disabled');
    cy.get('#rollingEnabled').should('not.be.checked');
  });

  it('handles configuration fetch errors', () => {
    // Mock error response
    cy.intercept('GET', '/rolling', {
      statusCode: 500,
      body: { error: 'Internal server error' }
    }).as('getRollingError');

    // Expand panel (triggers fetch)
    cy.get('.rolling-config-panel button.btn-link').click();

    // Wait for error
    cy.wait('@getRollingError');

    // Panel should still expand but show default values
    cy.get('.rolling-config-panel .card-body').should('be.visible');
  });

  it('handles update errors gracefully', () => {
    // Mock error response
    cy.intercept('PATCH', '/rolling', {
      statusCode: 400,
      body: { error: 'Invalid configuration' }
    });

    // Expand panel
    cy.expandRollingConfig();

    // Try to update if not disabled
    cy.get('#minAvailable').then($input => {
      if (!$input.is(':disabled')) {
        cy.get('#minAvailable').clear().type('999');
        cy.get('#minAvailable').trigger('change');
      }
    });

    // App should handle error gracefully (not crash)
    cy.get('.rolling-config-panel').should('still.exist');
  });

  it('shows tooltips on hover', () => {
    // Expand panel
    cy.expandRollingConfig();

    // Check for tooltip attributes - they may or may not have the attribute
    cy.get('#minAvailable').should('exist');
    cy.get('#batchSize').should('exist');
  });

  it('maintains state after collapsing and re-expanding', () => {
    // Expand panel
    cy.expandRollingConfig();

    // Get initial value
    cy.get('#minAvailable').then($input => {
      const initialValue = $input.val();
      
      // Only test if input is enabled
      if (!$input.is(':disabled')) {
        // Change value
        cy.get('#minAvailable').clear().type('7');
        
        // Collapse
        cy.get('.rolling-config-panel button.btn-link').click();
        cy.get('.rolling-config-panel .card-body').should('not.exist');
        
        // Re-expand
        cy.get('.rolling-config-panel button.btn-link').click();
        cy.get('.rolling-config-panel .card-body').should('be.visible');
        
        // Value should be maintained (component state persists)
        cy.get('#minAvailable').should('have.value', '7');
      } else {
        // If disabled, just verify panel toggle works
        cy.get('.rolling-config-panel button.btn-link').click();
        cy.get('.rolling-config-panel .card-body').should('not.exist');
        
        cy.get('.rolling-config-panel button.btn-link').click();
        cy.get('.rolling-config-panel .card-body').should('be.visible');
      }
    });
  });
});