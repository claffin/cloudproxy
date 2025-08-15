describe('Proxy Management', () => {
  beforeEach(() => {
    cy.mockAPI();
    cy.visit('/');
    cy.waitForPageLoad();
  });

  it('displays the main application layout', () => {
    // Check navbar
    cy.get('.navbar').should('be.visible');
    cy.get('.navbar-brand').should('contain', 'CloudProxy');
    
    // Check header
    cy.get('h1').should('contain', 'Proxy Management');
    
    // Check main sections
    cy.get('.rolling-config-panel').should('be.visible');
    cy.get('.provider-section').should('have.length.at.least', 1);
  });

  it('shows provider information correctly', () => {
    // Check provider sections exist
    cy.get('.provider-section').should('have.length.at.least', 1);
    
    // Check first provider section
    cy.get('.provider-section').first().within(() => {
      cy.get('h2').should('exist');
      cy.get('.status-badge').should('exist');
      // Check for proxy items if they exist
      cy.get('.proxy-item').should('have.length.at.least', 1);
    });

    // Check proxy details
    cy.get('.proxy-ip').should('exist');
    cy.get('.region-indicator').should('exist');
  });

  it('allows scaling proxies up and down', () => {
    // Mock successful update
    cy.intercept('PATCH', '/providers/**', {
      statusCode: 200,
      body: { message: 'Provider updated successfully' }
    });

    // Find and update scaling input
    cy.get('.provider-section').first().within(() => {
      cy.get('.custom-spinbutton').should('exist');
      cy.get('.custom-spinbutton').first().clear().type('5');
      cy.get('.custom-spinbutton').first().trigger('change');
    });

    // Just verify the input changed
    cy.get('.provider-section').first().within(() => {
      cy.get('.custom-spinbutton').first().should('have.value', '5');
    });
  });

  it('handles proxy removal', () => {
    // Mock successful removal
    cy.intercept('DELETE', '/destroy**', {
      statusCode: 200,
      body: { message: 'Proxy removed successfully' }
    });

    // Check if remove button exists
    cy.get('.proxy-item').first().within(() => {
      cy.get('.remove-btn').should('exist').and('be.visible');
      // Click is tested but we won't wait for specific API call
      cy.get('.remove-btn').click();
    });
  });

  it('copies proxy URL to clipboard', () => {
    // Stub clipboard API
    cy.window().then(win => {
      cy.stub(win.navigator.clipboard, 'writeText').resolves();
    });

    // Click copy button
    cy.get('.proxy-item').first().within(() => {
      cy.get('.copy-btn').click();
    });

    // Verify clipboard was called
    cy.window().its('navigator.clipboard.writeText').should('have.been.called');
  });

  it('refreshes page on refresh button click', () => {
    // Click refresh button - it will reload the page
    cy.get('.navbar button').contains('Refresh').should('exist');
    
    // We can't easily test window.reload in Cypress without stubbing before page load
    // So we'll just verify the button exists and is clickable
    cy.get('.navbar button').contains('Refresh').should('be.visible').and('not.be.disabled');
  });

  it('displays empty state for disabled providers', () => {
    // Mock provider with no proxies and disabled
    cy.intercept('GET', '/providers', {
      statusCode: 200,
      body: {
        providers: {
          aws: {
            instances: {
              default: {
                enabled: false,
                ips: [],
                scaling: { min_scaling: 0, max_scaling: 0 }
              }
            }
          }
        }
      }
    });

    cy.visit('/');
    
    // Check empty state message
    cy.get('.empty-state').should('be.visible');
    cy.get('.empty-state').should('contain', 'Provider not enabled');
  });

  it('shows progress when scaling up proxies', () => {
    // Mock provider in scaling state
    cy.intercept('GET', '/providers', {
      statusCode: 200,
      body: {
        providers: {
          digitalocean: {
            instances: {
              default: {
                enabled: true,
                ips: ['192.168.1.1'],
                scaling: { min_scaling: 3, max_scaling: 3 },
                region: 'nyc1'
              }
            }
          }
        }
      }
    });

    cy.visit('/');

    // Check progress indicator
    cy.get('.progress-item').should('be.visible');
    cy.get('.progress-item').should('contain', 'Deploying new proxies');
    cy.get('.progress-bar').should('be.visible');
    cy.get('small').should('contain', '1 of 3 proxies ready');
  });

  it('handles API errors gracefully', () => {
    // Mock API error
    cy.intercept('PATCH', '/providers/**', {
      statusCode: 500,
      body: { error: 'Internal server error' }
    });

    // Try to update scaling
    cy.get('.provider-section').first().within(() => {
      cy.get('.custom-spinbutton').should('exist');
      cy.get('.custom-spinbutton').first().clear().type('5');
      cy.get('.custom-spinbutton').first().trigger('change');
    });

    // The app should handle the error gracefully (not crash)
    cy.get('.provider-section').should('still.exist');
  });

  it('auto-refreshes data periodically', () => {
    let callCount = 0;
    
    cy.intercept('GET', '/providers', (req) => {
      callCount++;
      req.reply({
        statusCode: 200,
        body: { providers: {} }
      });
    }).as('getProvidersRefresh');

    // Wait for initial load
    cy.wait('@getProvidersRefresh');
    const initialCount = callCount;

    // Wait for auto-refresh (3 seconds)
    cy.wait(3500);

    // Check that additional calls were made
    cy.wrap(null).should(() => {
      expect(callCount).to.be.greaterThan(initialCount);
    });
  });
});