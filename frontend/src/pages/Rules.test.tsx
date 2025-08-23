import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import Rules from './Rules';

const mockRules = [
  {
    id: 1,
    label: 'Food',
    pattern: 'Tesco',
    match_type: 'contains',
    field: 'description',
    priority: 1,
    confidence: 1,
    version: 1,
    provenance: 'test',
    updated_at: 'now',
  },
];

describe('Rules page', () => {
  beforeEach(() => {
    global.fetch = vi.fn((url: RequestInfo, opts?: RequestInit) => {
      if (url === '/rules') {
        return Promise.resolve(
          new Response(JSON.stringify(mockRules), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }),
        );
      }
      if (url === '/feedback') {
        return Promise.resolve(new Response(null, { status: 200 }));
      }
      return Promise.reject(new Error('unknown url'));
    }) as any;
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('validates empty suggestion', async () => {
    render(<Rules />);
    const button = await screen.findByRole('button', {
      name: /suggest correction/i,
    });
    fireEvent.click(button);
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Suggestion is required',
    );
    // only initial /rules fetch
    expect((global.fetch as any).mock.calls).toHaveLength(1);
  });

  it('submits suggestion to /feedback', async () => {
    render(<Rules />);
    const input = await screen.findByLabelText('Suggestion');
    fireEvent.change(input, { target: { value: 'Groceries' } });
    const button = screen.getByRole('button', { name: /suggest correction/i });
    fireEvent.click(button);
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/feedback',
        expect.objectContaining({ method: 'POST' }),
      );
    });
  });
});
