"use client";

import * as React from "react";
import { Menu, BookOpen, GitCompare, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

interface NavbarProps {
  view: "home" | "detail" | "compare";
  onNavigate: (view: "home" | "compare") => void;
}

export function Navbar({ view, onNavigate }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const navItems = [
    { id: "home" as const, label: "Encyclopedia", icon: BookOpen },
    { id: "compare" as const, label: "Compare", icon: GitCompare },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav
        className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8"
        aria-label="Primary"
      >
        {/* Logo */}
        <button
          type="button"
          onClick={() => onNavigate("home")}
          className="flex items-center gap-2 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="WildAtlas home"
        >
          <span className="text-xl" aria-hidden="true">
            🦁
          </span>
          <span className="text-lg font-bold tracking-tight">WildAtlas</span>
        </button>

        {/* Desktop nav */}
        <div className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              (item.id === "home" && view === "home") ||
              (item.id === "home" && view === "detail") ||
              (item.id === "compare" && view === "compare");
            return (
              <Button
                key={item.id}
                type="button"
                variant={isActive ? "secondary" : "ghost"}
                size="sm"
                onClick={() => onNavigate(item.id)}
                className="gap-2"
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </Button>
            );
          })}
        </div>

        <div className="flex items-center gap-1">
          <ThemeToggle />

          {/* Mobile menu */}
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 md:hidden"
                aria-label="Open menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <SheetHeader>
                <SheetTitle className="flex items-center gap-2">
                  <span aria-hidden="true">🦁</span> WildAtlas
                </SheetTitle>
              </SheetHeader>
              <div className="mt-6 flex flex-col gap-2 px-4">
                <SheetClose asChild>
                  <Button
                    variant={view === "home" || view === "detail" ? "secondary" : "ghost"}
                    className="justify-start gap-3"
                    onClick={() => onNavigate("home")}
                  >
                    <Home className="h-4 w-4" /> Encyclopedia
                  </Button>
                </SheetClose>
                <SheetClose asChild>
                  <Button
                    variant={view === "compare" ? "secondary" : "ghost"}
                    className="justify-start gap-3"
                    onClick={() => onNavigate("compare")}
                  >
                    <GitCompare className="h-4 w-4" /> Compare Animals
                  </Button>
                </SheetClose>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </header>
  );
}
