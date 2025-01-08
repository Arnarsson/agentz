'use client';

import { SignedIn, SignedOut, useUser } from "@clerk/nextjs";
import TokenDisplay from "./components/TokenDisplay";

export default function Home() {
  const { user } = useUser();

  return (
    <main className="flex min-h-screen flex-col items-center p-24">
      <div className="max-w-5xl w-full">
        <SignedOut>
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold">Welcome to AgentZ</h1>
            <p className="text-xl text-gray-600">Sign in to get started</p>
          </div>
        </SignedOut>
        
        <SignedIn>
          <div className="space-y-8">
            <div className="space-y-2">
              <h1 className="text-4xl font-bold">Welcome, {user?.firstName || 'User'}!</h1>
              <p className="text-xl text-gray-600">Your AI Agent Dashboard</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Quick Actions */}
              <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
                <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
                <div className="space-y-3">
                  <button className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                    Create New Agent
                  </button>
                  <button className="w-full py-2 px-4 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition">
                    View Active Agents
                  </button>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
                <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
                <div className="space-y-3">
                  <p className="text-gray-600">No recent activity</p>
                </div>
              </div>

              {/* System Status */}
              <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
                <h2 className="text-xl font-semibold mb-4">System Status</h2>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span>API Status</span>
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-sm">Operational</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Active Agents</span>
                    <span className="text-gray-600">0</span>
                  </div>
                </div>
              </div>

              {/* Resources */}
              <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
                <h2 className="text-xl font-semibold mb-4">Resources</h2>
                <div className="space-y-3">
                  <a href="#" className="block text-blue-600 hover:underline">Documentation</a>
                  <a href="#" className="block text-blue-600 hover:underline">API Reference</a>
                  <a href="#" className="block text-blue-600 hover:underline">Support</a>
                </div>
              </div>
            </div>

            {/* Token Display */}
            <TokenDisplay />
          </div>
        </SignedIn>
      </div>
    </main>
  );
} 