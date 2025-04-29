'use client';

import { useState } from 'react';
import { CheckCheck, Copy } from 'lucide-react';

interface CodeBlockProps {
  code: string;
}

export default function CodeBlock({ code }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy!', err);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={handleCopy}
        aria-label="Copy code"
        className="absolute top-2 right-2 rounded bg-white p-1 shadow hover:bg-gray-100"
      >
        {copied ? <CheckCheck className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4 text-gray-500" />}
      </button>
      <pre className="overflow-x-auto bg-gray-100 p-4 rounded">
        <code className="whitespace-pre">{code}</code>
      </pre>
    </div>
  );
}
