'use client';

import { useAuth } from '@clerk/nextjs';
import { useState } from 'react';

export default function TokenDisplay() {
  const { getToken } = useAuth();
  const [token, setToken] = useState<string>('');
  const [showToken, setShowToken] = useState(false);

  const fetchAndDisplayToken = async () => {
    const jwt = await getToken();
    setToken(jwt || 'No token found');
    setShowToken(true);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(token);
  };

  return (
    <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 mt-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">JWT Token</h3>
        <button
          onClick={fetchAndDisplayToken}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          {showToken ? 'Refresh Token' : 'Show Token'}
        </button>
      </div>
      
      {showToken && (
        <div className="space-y-3">
          <div className="relative">
            <pre className="bg-gray-800 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
              {token}
            </pre>
            <button
              onClick={copyToClipboard}
              className="absolute top-2 right-2 px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 text-sm"
            >
              Copy
            </button>
          </div>
          <p className="text-sm text-gray-600">
            This is your session JWT token. You can use it for API authentication.
          </p>
        </div>
      )}
    </div>
  );
} 