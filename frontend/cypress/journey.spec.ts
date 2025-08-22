// Three-click journey: upload -> progress -> results
// Uses Cypress to simulate user interactions and network responses.

describe('user can upload file and reach results', () => {
  it('navigates through upload, progress and results pages', () => {
    cy.intercept('GET', '/rules', ['rule one']);
    cy.visit('/');

    cy.intercept('POST', '/upload', { job_id: '123' }).as('upload');
    let statusCall = 0;
    cy.intercept('GET', '/status/123', (req) => {
      statusCall += 1;
      if (statusCall === 1) {
        req.reply({ status: 'uploaded' });
      } else {
        req.reply({ status: 'completed' });
      }
    }).as('status');
    cy.intercept('POST', '/classify', {}).as('classify');
    cy.intercept('GET', '/download/123/summary', { body: 'summary' });
    cy.intercept('GET', '/download/123/report', { body: 'report' });
    cy.intercept('GET', '/summary/123', {
      totals: { income: 0, expenses: 0, net: 0 },
      categories: [],
      recurring: [],
    });
    cy.intercept('GET', '/transactions/123', []);

    const filePath = 'cypress/fixtures/sample.jsonl';
    cy.get('input[type="file"]').selectFile(filePath);
    cy.contains('button', /upload/i).click();

    cy.wait('@upload');
    cy.contains(/job id/i).should('contain', '123');
    cy.wait('@status');
    cy.wait('@classify');
    cy.url().should('include', '/progress/123');
    cy.get('[role="status"]').should('be.visible');

    cy.url().should('include', '/results/123');
    cy.contains('a', /summary/i).should('be.visible');
    cy.contains('a', /report/i).should('be.visible');
  });
});

