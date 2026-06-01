import { useEffect } from "react";

interface PageTitleProps {
  title: string;
}

export default function PageTitle({ title }: PageTitleProps) {
  useEffect(() => {
    const defaultTitle = "Wedding Planner";
    
    document.title = `${title} | ${defaultTitle}`;

    return () => {
      document.title = defaultTitle;
    };
  }, [title]);

  return null;
}