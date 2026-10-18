import { Outlet, useLocation } from 'react-router-dom';
import { navigationItems } from '../app/navigation';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import MobileNavigation from './MobileNavigation';

function AppShell() {
  const location = useLocation();

  const currentPage = navigationItems.find(
    (item) =>
      item.path === location.pathname ||
      (item.path !== '/' && location.pathname.startsWith(`${item.path}/`)),
  );

  const pageTitle = currentPage?.label ?? 'Not Found';

  return (
    <div className="app-shell">
      <Sidebar />

      <div className="app-shell__main">
        <TopBar title={pageTitle} />

        <main className="app-shell__content">
          <Outlet />
        </main>
      </div>

      <MobileNavigation />
    </div>
  );
}

export default AppShell;