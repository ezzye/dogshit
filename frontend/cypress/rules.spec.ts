describe('rules list', () => {
  it('renders rule details without [object Object]', () => {
    cy.intercept('GET', '/rules', [
      {
        id: 1,
        user_id: 1,
        label: 'Food',
        pattern: 'Coffee',
        match_type: 'contains',
        field: 'description',
        priority: 0,
        confidence: 1,
        version: 1,
        provenance: 'user',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]);
    cy.visit('/');
    cy.get('li')
      .first()
      .should('contain', 'Coffee')
      .and('contain', 'Food')
      .and('not.contain', '[object Object]');
  });
});

