export interface NavigationItem {
  label: string;
  path: string;
  section: 'main' | 'system';
  description: string;
}

export const navigationItems: NavigationItem[] = [
  {
    label: 'Overview',
    path: '/',
    section: 'main',
    description: 'Cluster overview',
  },
  {
    label: 'Workers',
    path: '/workers',
    section: 'main',
    description: 'Registered compute nodes',
  },
  {
    label: 'Jobs',
    path: '/jobs',
    section: 'main',
    description: 'Workload queue and results',
  },
  {
    label: 'Join network',
    path: '/workers/register',
    section: 'main',
    description: 'Configure a contributing computer',
  },
  {
    label: 'Settings',
    path: '/settings',
    section: 'system',
    description: 'Controller configuration',
  },
];