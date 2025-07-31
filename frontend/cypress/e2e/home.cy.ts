describe('home page', () => {
  it('loads', () => {
    cy.visit('/');
    cy.contains('Heuristic Editor');
    cy.contains('Pattern expects a regular expression');
  });
});
