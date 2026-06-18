// src/pages/ProfilePage.tsx
import React from 'react';

export const ProfilePage: React.FC = () => {
  // Hardcoded or pulled dynamically from an auth store
  const currentUserId = "12345"; 

  return (
    <main className="container mx-auto p-6">
      <h1 className="text-3xl font-semibold mb-4">Account Overview</h1>
    </main>
  );
};
