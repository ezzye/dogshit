import React from 'react';

interface ReportViewerProps {
  url: string | null;
}

export default function ReportViewer({ url }: ReportViewerProps) {
  if (!url) return null;
  return (
    <iframe
      src={url}
      title="Report"
      className="w-full h-[80vh] border"
    />
  );
}

