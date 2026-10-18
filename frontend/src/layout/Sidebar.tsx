import { NavLink } from 'react-router-dom';
import { navigationItems } from '../app/navigation';

function Sidebar() {
  const mainItems = navigationItems.filter(
    (item) => item.section === 'main',
  );

  const systemItems = navigationItems.filter(
    (item) => item.section === 'system',
  );

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark" aria-hidden="true">
          D
        </div>

        <div>
          <p className="sidebar__brand-name">DABALLS</p>
          <p className="sidebar__brand-caption">COMPUTE CONTROL</p>
        </div>
      </div>

      <div className="sidebar__environment">
        <span className="sidebar__environment-dot" />
        LOCAL ENVIRONMENT
      </div>

      <nav className="sidebar__nav" aria-label="Main navigation">
        <p className="sidebar__section-label">WORKSPACE</p>

        {mainItems.map((item, index) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `sidebar__link${isActive ? ' sidebar__link--active' : ''}`
            }
          >
            <span className="sidebar__link-index">
              {String(index + 1).padStart(2, '0')}
            </span>
            <span>{item.label}</span>
          </NavLink>
        ))}

        <p className="sidebar__section-label sidebar__section-label--system">
          SYSTEM
        </p>

        {systemItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar__link${isActive ? ' sidebar__link--active' : ''}`
            }
          >
            <span className="sidebar__link-index">··</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <footer className="sidebar__footer">
        <span className="sidebar__footer-line" />
        <p>Distributed computing</p>
        <p>Built node by node.</p>
      </footer>
    </aside>
  );
}

export default Sidebar;