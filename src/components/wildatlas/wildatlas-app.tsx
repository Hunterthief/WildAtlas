"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Navbar } from "./navbar";
import { Footer } from "./footer";
import { HomeView } from "./home-view";
import { AnimalDetailView } from "./animal-detail-view";
import { CompareView } from "./compare-view";

/**
 * WildAtlas app shell.
 *
 * Routing via URL search params (shareable deep links):
 *   - Home:     /
 *   - Detail:   /?name=Tiger                       (curated)
 *               /?name=Blue%20whale&wiki=Blue%20whale&type=mammal  (on-demand)
 *   - Compare:  /?compare=Tiger,Cheetah            (curated names)
 *               /?compare=Blue whale,Orca&wikis=Blue whale,Orca&types=mammal,mammal
 */
export interface AnimalRef {
  name: string;
  wikipediaTitle?: string;
  type?: string;
  featured?: boolean;
}

export function WildAtlasApp() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const nameParam = searchParams.get("name");
  const wikiParam = searchParams.get("wiki");
  const typeParam = searchParams.get("type");
  const compareParam = searchParams.get("compare");
  const compareWikis = searchParams.get("wikis");
  const compareTypes = searchParams.get("types");

  const view: "home" | "detail" | "compare" = nameParam
    ? "detail"
    : compareParam !== null
      ? "compare"
      : "home";

  // Persist compare selections in the URL
  const handleCompareRefsChange = React.useCallback(
    (refs: AnimalRef[]) => {
      const params = new URLSearchParams();
      if (refs.length > 0) {
        params.set("compare", refs.map((r) => r.name).join(","));
        const wikis = refs.map((r) => r.wikipediaTitle).filter(Boolean);
        const types = refs.map((r) => r.type).filter(Boolean);
        const featured = refs.map((r) => (r.featured ? "1" : "0"));
        if (wikis.length) params.set("wikis", wikis.join(","));
        if (types.length) params.set("types", types.join(","));
        params.set("feat", featured.join(","));
      } else {
        params.set("compare", "1");
      }
      router.replace(`/?${params.toString()}`, { scroll: false });
    },
    [router],
  );

  const goHome = React.useCallback(() => {
    router.push("/", { scroll: true });
  }, [router]);

  const goCompare = React.useCallback(() => {
    router.push("/?compare=1", { scroll: true });
  }, [router]);

  const selectAnimal = React.useCallback(
    (animalName: string, wikipediaTitle?: string, type?: string, featured?: boolean) => {
      // Store extra info in sessionStorage to keep the URL clean (avoids
      // Turbopack dev-server crashes on complex query strings). On GitHub
      // Pages (static), URLs with params work fine, but this is safer.
      if (wikipediaTitle || type) {
        try {
          sessionStorage.setItem(
            `animal:${animalName.toLowerCase()}`,
            JSON.stringify({ wikipediaTitle, type, featured }),
          );
        } catch {}
      }
      const params = new URLSearchParams();
      params.set("name", animalName);
      if (featured) params.set("featured", "1");
      router.push(`/?${params.toString()}`, { scroll: true });
    },
    [router],
  );

  // Parse initial compare refs from the URL
  const initialCompareRefs = React.useMemo<AnimalRef[]>(() => {
    if (!compareParam || compareParam === "1") return [];
    const names = compareParam.split(",").map((n) => decodeURIComponent(n.trim())).filter(Boolean);
    const wikis = (compareWikis ?? "").split(",").map((w) => decodeURIComponent(w.trim()));
    const types = (compareTypes ?? "").split(",").map((t) => decodeURIComponent(t.trim()));
    const feats = (searchParams.get("feat") ?? "").split(",");
    return names.map((name, i) => ({
      name,
      wikipediaTitle: wikis[i] || undefined,
      type: types[i] || undefined,
      featured: feats[i] === "1",
    }));
  }, [compareParam, compareWikis, compareTypes, searchParams]);

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-primary-foreground"
      >
        Skip to content
      </a>

      <Navbar
        view={view}
        onNavigate={(target) => (target === "home" ? goHome() : goCompare())}
      />

      <main id="main-content" className="flex-1">
        {view === "home" && <HomeView onSelectAnimal={selectAnimal} />}
        {view === "detail" && nameParam && (() => {
          // Read extra info from sessionStorage (set by selectAnimal) or URL params
          let wikiTitle = wikiParam ?? undefined;
          let typeVal = typeParam ?? undefined;
          let featured = searchParams.get("featured") === "1";
          try {
            const stored = sessionStorage.getItem(`animal:${nameParam.toLowerCase()}`);
            if (stored) {
              const parsed = JSON.parse(stored);
              wikiTitle = wikiTitle ?? parsed.wikipediaTitle;
              typeVal = typeVal ?? parsed.type;
              featured = featured || !!parsed.featured;
            }
          } catch {}
          return (
          <AnimalDetailView
            name={nameParam}
            wikipediaTitle={wikiTitle}
            type={typeVal}
            featured={featured}
            onBack={goHome}
            onSelectAnimal={selectAnimal}
          />
          );
        })()}
        {view === "compare" && (
          <CompareView
            initialRefs={initialCompareRefs}
            onRefsChange={handleCompareRefsChange}
            onBack={goHome}
            onSelectAnimal={selectAnimal}
          />
        )}
      </main>

      <Footer />
    </div>
  );
}
