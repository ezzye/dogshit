import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ReportViewer from './ReportViewer';

describe('ReportViewer', () => {
  it('renders iframe when url is provided', () => {
    render(<ReportViewer url="https://example.com/report.pdf" />);
    const iframe = screen.getByTitle('Report');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'https://example.com/report.pdf');
  });

  it('renders nothing when url is null', () => {
    const { container } = render(<ReportViewer url={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});

