describe('results page summary', () => {
  it('renders summary table and download links', () => {
    cy.intercept('GET', '/summary/123', {
      totals: { income: 100, expenses: 50, net: 50 },
      categories: [{ name: 'Food', total: 20, count: 2 }],
      recurring: [{ merchant: 'Gym', cadence: 'monthly', avg_amount: 30, count: 3 }],
    });
    cy.intercept('GET', '/transactions/123', [
      { date: '2024-01-01', description: 'Coffee', amount: 3, type: 'debit' },
    ]);
    cy.visit('/results/123');
    cy.get('a[href="/download/123/summary"]').should('exist');
    cy.get('a[href="/download/123/report"]').should('exist');
    cy.contains('td', 'Income').next().should('contain', '100');
    cy.contains('td', 'Expenses').next().should('contain', '50');
    cy.contains('td', 'Net').next().should('contain', '50');
    cy.contains('td', 'Food').should('be.visible');
    cy.contains('td', 'Coffee').should('be.visible');
  });
});
