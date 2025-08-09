// Three-click journey: upload -> progress -> results
// Uses Cypress to simulate user interactions and network responses.

describe('user can upload file and reach results', () => {
  it('navigates through upload, progress and results pages', () => {
    cy.intercept('GET', '/rules', ['rule one']);
    cy.visit('/');

    cy.intercept('POST', '/upload', { job_id: '123' });
    cy.intercept('GET', '/status/123', { status: 'completed' });
    cy.intercept('GET', '/download/123/summary', { body: 'summary' });
    cy.intercept('GET', '/download/123/details', { body: 'details' });

    const filePath = 'index.html';
    cy.get('input[type="file"]').selectFile(filePath);
    cy.contains('button', /upload/i).click();

    cy.url().should('include', '/progress/123');
    cy.get('[role="status"]').should('be.visible');

    cy.url().should('include', '/results/123');
    cy.contains('a', /summary/i).should('be.visible');
    cy.contains('a', /details/i).should('be.visible');
  });
});

