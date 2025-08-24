describe('rules list', () => {
  it('renders rule details without [object Object]', () => {
    cy.intercept('GET', '/rules', (req) => {
      if (req.headers['sec-fetch-dest'] === 'empty') {
        req.reply([
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
      }
    });
    cy.visit('/rules');
    cy.get('ul li')
      .first()
      .should('contain', 'Coffee')
      .and('contain', 'Food')
      .and('not.contain', '[object Object]');
  });
});

