describe('heuristic editor', () => {
  it('user uploads JSONL -> edits rule -> saves -> sees confirmation', () => {
    cy.intercept('POST', '/upload', { statusCode: 200, body: { count: 1 } });
    cy.intercept('GET', '/heuristics', { fixture: 'initial.json' });
    cy.intercept('POST', '/heuristics', { body: { id: 1, label: 'coffee', pattern: 'coffee' } });

    cy.visit('/');

    cy.fixture('tx.jsonl').then((content) => {
      const blob = new Blob([content], { type: 'application/jsonl' });
      const file = new File([blob], 'tx.jsonl');
      cy.get('input[type=file]').first().selectFile({ contents: file, fileName: 'tx.jsonl' });
    });

    cy.get('tbody tr').eq(0).find('input').first().clear().type('coffee');
    cy.get('tbody tr').eq(0).find('button').contains('Save').click();
    cy.contains('Saved');
  });
});
