import { useState, useRef, useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import styles from "./Navbar.module.css";

const NAV_ITEMS = [
  { label: "Wydarzenie", to: "/event" },
  { label: "Goście", to: "/guests" },
  { label: "Stoły", to: "/tables" },
  { label: "Zaproszenia", to: "/invitations" },
  { label: "Finanse", to: "/finances" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const [accountOpen, setAccountOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const dropdownRef = useRef<HTMLLIElement>(null);
  const mobileMenuRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setAccountOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const closeMobileMenu = () => setMobileOpen(false);

  const handleLogout = () => {
    setAccountOpen(false);
    closeMobileMenu();
    logout();
    navigate("/login");
  };

  return (
    <header className={styles.header}>
      <nav className={styles.nav}>
        {/* Logo */}
        <NavLink to="/dashboard" className={styles.logo}>
          <span className={styles.logoIcon}>💍</span>
          <span className={styles.logoText}>WeddingPlanner</span>
        </NavLink>

        {/* Hamburger button */}
        <button
          className={styles.hamburger}
          onClick={() => setMobileOpen((prev) => !prev)}
          aria-label="Menu"
          aria-expanded={mobileOpen}
        >
          <span className={styles.hamburgerLine} />
          <span className={styles.hamburgerLine} />
          <span className={styles.hamburgerLine} />
        </button>

        {/* Desktop menu */}
        <ul className={`${styles.navList} ${mobileOpen ? styles.navListOpen : ""}`} ref={mobileMenuRef}>
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  `${styles.navLink} ${isActive ? styles.navLinkActive : ""}`
                }
                onClick={closeMobileMenu}
              >
                {item.label}
              </NavLink>
            </li>
          ))}

          {/* My Account – dropdown (desktop) / regular link (mobile) */}
          <li className={styles.accountWrapper} ref={dropdownRef}>
            {mobileOpen ? (
              <>
                <NavLink
                  to="/account"
                  className={({ isActive }) =>
                    `${styles.navLink} ${isActive ? styles.navLinkActive : ""}`
                  }
                  onClick={closeMobileMenu}
                >
                  Moje konto
                </NavLink>
                <button
                  className={`${styles.navLink} ${styles.logoutMobileBtn}`}
                  onClick={handleLogout}
                >
                  Wyloguj
                </button>
              </>
            ) : (
              <>
                <button
                  className={`${styles.navLink} ${styles.accountBtn} ${accountOpen ? styles.navLinkActive : ""}`}
                  onClick={() => setAccountOpen((prev) => !prev)}
                  aria-expanded={accountOpen}
                  aria-haspopup="true"
                >
                  Moje konto
                  <span className={`${styles.chevron} ${accountOpen ? styles.chevronOpen : ""}`}>
                    ▾
                  </span>
                </button>

                {accountOpen && (
                  <div className={styles.dropdown} role="menu">
                    <NavLink
                      to="/account"
                      className={styles.dropdownItem}
                      onClick={() => setAccountOpen(false)}
                      role="menuitem"
                    >
                      <span className={styles.dropdownIcon}>👤</span>
                      Moje konto
                    </NavLink>
                    <div className={styles.dropdownDivider} />
                    <button
                      className={`${styles.dropdownItem} ${styles.dropdownItemDanger}`}
                      onClick={handleLogout}
                      role="menuitem"
                    >
                      <span className={styles.dropdownIcon}>🚪</span>
                      Wyloguj
                    </button>
                  </div>
                )}
              </>
            )}
          </li>
        </ul>
      </nav>
    </header>
  );
}