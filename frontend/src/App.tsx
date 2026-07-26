import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ChatPage } from './pages/ChatPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { MetricsPage } from './pages/MetricsPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsPage } from './pages/SettingsPage';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { RouteErrorFallback } from './components/common/ErrorBoundary';

const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/app/chat" replace />, errorElement: <RouteErrorFallback /> },
  { path: '/login', element: <LoginPage />, errorElement: <RouteErrorFallback /> },
  { path: '/register', element: <RegisterPage />, errorElement: <RouteErrorFallback /> },
  {
    element: <ProtectedRoute />,
    errorElement: <RouteErrorFallback />,
    children: [{
      path: '/app',
      element: <AppLayout />,
      errorElement: <RouteErrorFallback />,
      children: [
      { index: true, element: <Navigate to="/app/chat" replace /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'data-sources', element: <DataSourcesPage /> },
      { path: 'metrics', element: <MetricsPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'settings', element: <SettingsPage /> },
      ],
    }],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
