import type { ReactNode } from "react";
import Navbar from "./Navbar";
import styles from "./Layout.module.css";

interface Props {
  children: ReactNode;
}

export default function Layout({ children }: Props) {
  return (
    <div className={styles.root}>
      <Navbar />
      <main className={styles.main}>{children}</main>
    </div>
  );
}