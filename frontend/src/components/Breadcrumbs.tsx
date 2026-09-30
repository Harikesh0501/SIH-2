import React from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav className="flex items-center space-x-1.5 text-xs text-zinc-500 mb-4" aria-label="Breadcrumb">
      <Link href="/" className="hover:text-zinc-900 transition-colors">
        Home
      </Link>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <ChevronRight className="w-3 h-3 text-zinc-400" />
          {item.href ? (
            <Link href={item.href} className="hover:text-zinc-900 transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="font-medium text-zinc-900">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}
