import type { ReactNode } from "react";

type CardProps = {
  children: ReactNode;
  className?: string;
};

export function Card({ children, className = "" }: CardProps) {
  return (
    <section
      className={`rounded-2xl border border-zinc-200/80 bg-white/90 p-6 shadow-sm shadow-zinc-900/[0.03] backdrop-blur-sm transition-shadow hover:shadow-md hover:shadow-zinc-900/[0.05] dark:border-zinc-800/80 dark:bg-zinc-900/90 dark:shadow-black/10 dark:hover:shadow-black/20 ${className}`}
    >
      {children}
    </section>
  );
}
