import { NavLink } from 'react-router-dom';
import { navigationItems } from '../app/navigation';

function MobileNavigation() {
  return (
    <nav className="mobile-navigation" aria-label="Mobile navigation">
      {navigationItems
        .filter((item) => item.section === 'main')
        .map((item, index) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `mobile-navigation__link${
                isActive ? ' mobile-navigation__link--active' : ''
              }`
            }
          >
            <span className="mobile-navigation__index">
              {String(index + 1).padStart(2, '0')}
            </span>
            <span>{item.label}</span>
          </NavLink>
        ))}
    </nav>
  );
}

export default MobileNavigation;