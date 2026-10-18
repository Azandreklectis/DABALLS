import {
  createBrowserRouter,
  Navigate,
  type RouteObject,
} from 'react-router-dom';
import AppShell from '../layout/AppShell';
import PageHeader from '../layout/PageHeader';

function OverviewPlaceholder() {
  return (
    <PageHeader
      eyebrow="CLUSTER / OVERVIEW"
      title="Overview"
      description="A clear view of your distributed compute network."
    />
  );
}

function WorkersPlaceholder() {
  return (
    <PageHeader
      eyebrow="CLUSTER / NODES"
      title="Workers"
      description="Inspect registered workers and their offered resources."
    />
  );
}

function JobsPlaceholder() {
  return (
    <PageHeader
      eyebrow="CLUSTER / WORKLOADS"
      title="Jobs"
      description="Submit supported workloads and inspect their execution results."
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
      { path: 'workers', element: <WorkersPlaceholder /> },
      { path: 'jobs', element: <JobsPlaceholder /> },
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