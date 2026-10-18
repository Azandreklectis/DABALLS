import {
  createBrowserRouter,
  Navigate,
  type RouteObject,
} from 'react-router-dom';
import AppShell from '../layout/AppShell';
import PageHeader from '../layout/PageHeader';
import JobsPage from "../features/jobs/JobsPage";
import WorkersPage from "../features/workers/WorkersPage";
import WorkerRegistrationPage from "../features/workers/WorkerRegistrationPage";

function OverviewPlaceholder() {
  return (
    <PageHeader
      eyebrow="CLUSTER / OVERVIEW"
      title="Overview"
      description="A clear view of your distributed compute network."
    />
  );
}


function SettingsPlaceholder() {
  return (
    <PageHeader
      eyebrow="SYSTEM / CONFIGURATION"
      title="Settings"
      description="Review the controller connection and application configuration."
    />
  );
}

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
      { index: true, element: <OverviewPlaceholder /> },
      { path: 'workers/register', element: <WorkerRegistrationPage /> },
      { path: 'workers', element: <WorkersPage /> },
      { path: 'jobs', element: <JobsPage /> },
      { path: 'settings', element: <SettingsPlaceholder /> },
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