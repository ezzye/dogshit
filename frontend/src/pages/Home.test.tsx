import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Home from './Home';

describe('Home page', () => {
  it('Given a visitor, when they view the home page, then they see proposition, instructions and navigation buttons', () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole('heading', { name: /understand your spending/i }),
    ).toBeInTheDocument();
    const bankcleanr = screen.getByRole('link', { name: /bankcleanr/i });
    expect(bankcleanr).toHaveAttribute('href', 'https://bankcleanr.uwu.ai/');
    expect(screen.getByRole('link', { name: /^upload$/i })).toHaveAttribute(
      'href',
      '/upload',
    );
    expect(screen.getByRole('link', { name: /rules/i })).toHaveAttribute(
      'href',
      '/rules',
    );
  });
});
