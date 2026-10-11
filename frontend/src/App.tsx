import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { MainLayout } from './layouts/MainLayout';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
};

export default App;

