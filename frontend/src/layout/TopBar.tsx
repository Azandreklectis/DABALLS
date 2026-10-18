interface TopBarProps {
  title: string;
}

function TopBar({ title }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="topbar__breadcrumb">
        <span>DABALLS</span>
        <span className="topbar__separator">/</span>
        <span className="topbar__current">{title}</span>
      </div>

      <div className="topbar__connection">
        <span className="topbar__connection-dot" />
        <span>CONNECTION UNVERIFIED</span>
      </div>
    </header>
  );
}

export default TopBar;