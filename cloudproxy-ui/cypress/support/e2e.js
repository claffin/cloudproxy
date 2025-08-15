// ***********************************************************
// This file is processed and loaded automatically before test files.
// You can change the location of this file or turn off processing it.
// ***********************************************************

// Import commands.js
import './commands';

// Disable uncaught exception handling
Cypress.on('uncaught:exception', (err, runnable) => {
  // returning false here prevents Cypress from failing the test
  return false;
});