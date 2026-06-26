import Link from "next/link";

/** Site footer. Sits at the bottom of the viewport on short pages. */
export function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col items-center gap-2 px-4 py-8 text-center sm:px-6 lg:px-8">
        <p className="text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} WildAtlas Project. Data sourced from
          Wikipedia, iNaturalist &amp; Wikidata.
        </p>
        <p className="text-xs text-muted-foreground">
          Inspired by{" "}
          <Link
            href="https://www.facts.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary hover:underline"
          >
            Facts.app
          </Link>
        </p>
      </div>
    </footer>
  );
}
