import {
  createBrowserRouter,
  Navigate,
  type RouteObject,
} from 'react-router-dom';
import AppShell from '../layout/AppShell';
import OverviewPage from '../features/overview/OverviewPage';
import SettingsPage from '../features/settings/SettingsPage';
import PageHeader from '../layout/PageHeader';
import JobsPage from "../features/jobs/JobsPage";
import WorkersPage from "../features/workers/WorkersPage";
import WorkerRegistrationPage from "../features/workers/WorkerRegistrationPage";

function NotFoundPlaceholder() {
  return (
    <PageHeader
      eyebrow="ERROR / 404"
      title="Page not found"
      description="The requested page does not exist."
    />
  );
}

const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: 'workers/register', element: <WorkerRegistrationPage /> },
      { path: 'workers', element: <WorkersPage /> },
      { path: 'jobs', element: <JobsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: '*', element: <NotFoundPlaceholder /> },
    ],
  },
];

export const router = createBrowserRouter([
  ...routes,
  {
    path: '/home',
    element: <Navigate to="/" replace />,
  },
]);