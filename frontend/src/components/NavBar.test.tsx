import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import NavBar from './NavBar';
import '@testing-library/jest-dom';

describe('NavBar component', () => {
  it('Given the NavBar is rendered, when viewed, then it shows links and placeholders', () => {
    render(
      <MemoryRouter>
        <NavBar />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /upload/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /rules/i })).toBeInTheDocument();
    expect(screen.getByText(/results/i)).toBeInTheDocument();
    expect(screen.getByText(/progress/i)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /results/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /progress/i })).not.toBeInTheDocument();
  });
});
