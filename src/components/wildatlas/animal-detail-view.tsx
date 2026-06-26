"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Ruler,
  ArrowUpDown,
  Weight,
  Zap,
  Clock,
  BookOpen,
  MapPin,
  Shield,
  Timer,
  HeartPulse,
  Languages,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnimalImage } from "./animal-image";
import { DietIcons } from "./diet-icons";
import { ConservationBadge } from "./conservation-badge";
import { WorldMap } from "./world-map";
import { TimelineBar } from "./timeline-bar";
import { StatCard } from "./stat-card";
import { useAnimalDetail } from "@/hooks/use-animals";
import { displayValue, getTimelineData, hasValue } from "@/lib/animals";
import { buildArticleSections, buildFaqList } from "@/lib/animal-content";
import type { Animal } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AnimalDetailViewProps {
  name: string;
  wikipediaTitle?: string;
  type?: string;
  featured?: boolean;
  onBack: () => void;
  onSelectAnimal: (name: string, wikipediaTitle?: string, type?: string, featured?: boolean) => void;
}

export function AnimalDetailView({
  name,
  wikipediaTitle,
  type,
  featured,
  onBack,
  onSelectAnimal,
}: AnimalDetailViewProps) {
  const { data, isLoading, isError, error } = useAnimalDetail(name, {
    wikipediaTitle,
    type,
    featured,
  });

  if (isLoading) return <DetailSkeleton />;
  if (isError) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <p className="text-sm font-medium text-destructive">
          Couldn&apos;t load this animal.
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {error instanceof Error ? error.message : "Please try again later."}
        </p>
        <Button variant="outline" size="sm" className="mt-4" onClick={onBack}>
          Back to encyclopedia
        </Button>
      </div>
    );
  }

  // Pending: the watcher is fetching from Wikipedia + enriching with the LLM.
  // Show a fetching state; the hook polls automatically every 2s.
  if (data?.pending || !data?.animal) {
    return <FetchingState name={name} onBack={onBack} />;
  }

  const animal = data.animal;
  return <AnimalDetailContent animal={animal} onBack={onBack} onSelectAnimal={onSelectAnimal} />;
}

function AnimalDetailContent({
  animal,
  onBack,
  onSelectAnimal,
}: {
  animal: Animal;
  onBack: () => void;
  onSelectAnimal: (name: string, wikipediaTitle?: string, type?: string, featured?: boolean) => void;
}) {
  const eco = animal.ecology ?? {};
  const phys = animal.physical ?? {};
  const repro = animal.reproduction ?? {};
  const summary = animal.summary ?? animal.description ?? "";
  const articleSections = React.useMemo(() => buildArticleSections(animal), [animal]);
  const faqs = React.useMemo(() => buildFaqList(animal), [animal]);

  // Hero image gallery
  const gallery = React.useMemo(() => {
    const imgs = animal.images?.filter(Boolean) ?? [];
    const unique = Array.from(new Set([animal.image, ...imgs].filter(Boolean)));
    return unique;
  }, [animal.image, animal.images]);

  const [activeImage, setActiveImage] = React.useState(0);
  React.useEffect(() => setActiveImage(0), [animal.name]);

  const classificationRows: { label: string; value?: string }[] = [
    { label: "Kingdom", value: animal.classification?.kingdom },
    { label: "Phylum", value: animal.classification?.phylum },
    { label: "Class", value: animal.classification?.class },
    { label: "Order", value: animal.classification?.order },
    { label: "Family", value: animal.classification?.family },
    { label: "Genus", value: animal.classification?.genus },
    { label: "Species", value: animal.classification?.species },
  ].filter((r) => hasValue(r.value)) as { label: string; value?: string }[];

  const hasReproData =
    hasValue(repro.name_of_young) ||
    hasValue(animal.young_name) ||
    hasValue(animal.group_name) ||
    hasValue(repro.gestation_period) ||
    hasValue(repro.average_litter_size);

  const timeData = React.useMemo(() => getTimelineData(animal), [animal]);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Back link */}
      <button
        type="button"
        onClick={onBack}
        className="mb-8 inline-flex items-center gap-2 rounded-md text-sm text-muted-foreground transition-colors hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to encyclopedia
      </button>

      {/* Title */}
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
          {animal.name}
        </h1>
        <p className="mt-2 font-serif text-lg italic text-muted-foreground sm:text-xl">
          {animal.scientific_name}
        </p>
      </header>

      {/* Three column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[260px_1fr_260px] xl:gap-8">
        {/* LEFT SIDEBAR */}
        <aside className="order-2 flex flex-col gap-4 lg:order-1">
          {/* Diet */}
          <StatCard
            icon={<span aria-hidden="true">🍽️</span>}
            label="Food"
            value={
              <DietIcons
                diet={eco.diet}
                animalType={animal.animal_type}
                summary={summary}
              />
            }
          />
          <StatCard
            icon={<Ruler className="h-4 w-4" />}
            label="Length"
            value={displayValue(phys.length)}
          />
          <StatCard
            icon={<ArrowUpDown className="h-4 w-4" />}
            label="Height"
            value={displayValue(phys.height)}
          />
          <StatCard
            icon={<Weight className="h-4 w-4" />}
            label="Weight"
            value={displayValue(phys.weight)}
          />
          <StatCard
            icon={<Zap className="h-4 w-4" />}
            label="Speed"
            value={displayValue(phys.top_speed)}
          />
          <StatCard
            icon={<Clock className="h-4 w-4" />}
            label="Lifespan"
            value={displayValue(phys.lifespan)}
          />

          {/* Classification */}
          {classificationRows.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-4">
              <div className="mb-3 flex items-center gap-2 text-[0.7rem] uppercase tracking-wide text-muted-foreground">
                <BookOpen className="h-4 w-4" aria-hidden="true" />
                Classification
              </div>
              <table className="w-full border-collapse">
                <tbody>
                  {classificationRows.map((row) => (
                    <tr key={row.label} className="border-b border-border last:border-0">
                      <th
                        scope="row"
                        className="w-2/5 py-2 pr-2 text-left text-[0.65rem] font-medium uppercase tracking-wide text-muted-foreground"
                      >
                        {row.label}
                      </th>
                      <td className="py-2 text-sm text-foreground">{row.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </aside>

        {/* CENTER COLUMN */}
        <div className="order-1 flex flex-col gap-6 lg:order-2">
          {/* Hero image gallery */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-2xl shadow-black/30">
            <AnimalImage
              src={gallery[activeImage]}
              alt={`${animal.name} — image ${activeImage + 1} of ${gallery.length}`}
              fallbackLabel={animal.name}
              className="aspect-[4/3] w-full sm:aspect-[16/10]"
            />
          </div>

          {/* Thumbnails (only if more than one image) */}
          {gallery.length > 1 && (
            <div className="flex flex-wrap gap-2">
              {gallery.map((src, i) => (
                <button
                  key={src + i}
                  type="button"
                  onClick={() => setActiveImage(i)}
                  className={cn(
                    "overflow-hidden rounded-md border-2 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    i === activeImage
                      ? "border-primary"
                      : "border-border opacity-60 hover:opacity-100",
                  )}
                  aria-label={`View image ${i + 1}`}
                  aria-pressed={i === activeImage}
                >
                  <AnimalImage
                    src={src}
                    alt=""
                    fallbackLabel={animal.name}
                    className="h-14 w-14"
                  />
                </button>
              ))}
            </div>
          )}

          {/* External sources */}
          <div className="flex flex-wrap gap-2">
            {hasValue(animal.wikipedia_url) && (
              <SourceLink href={animal.wikipedia_url!} label="Wikipedia" />
            )}
            {hasValue(animal.wikidata_url) && (
              <SourceLink href={animal.wikidata_url!} label="Wikidata" />
            )}
            {hasValue(animal.eol_url) && (
              <SourceLink href={animal.eol_url!} label="EOL" />
            )}
          </div>
        </div>

        {/* RIGHT SIDEBAR */}
        <aside className="order-3 flex flex-col gap-4">
          {/* Location */}
          <InfoCard icon={<MapPin className="h-4 w-4" />} title="Location & Distribution">
            {hasValue(eco.locations) ? (
              <div className="flex flex-col gap-3">
                {hasValue(animal.distribution_image) ? (
                  <DistributionImage src={animal.distribution_image!} name={animal.name} />
                ) : (
                  <WorldMap locations={eco.locations} className="aspect-[2/1]" />
                )}
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {eco.locations}
                </p>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                Location data is not available for this species.
              </p>
            )}
          </InfoCard>

          {/* Conservation */}
          <InfoCard icon={<Shield className="h-4 w-4" />} title="Conservation Status">
            <ConservationBadge status={eco.conservation_status} className="mb-3" />
            {hasValue(eco.biggest_threat) && (
              <div className="border-t border-border pt-3">
                <div className="mb-1 text-[0.65rem] uppercase tracking-wide text-muted-foreground">
                  Biggest Threats
                </div>
                <p className="text-xs leading-relaxed text-foreground">
                  {eco.biggest_threat}
                </p>
              </div>
            )}
          </InfoCard>

          {/* Time period */}
          <InfoCard icon={<Timer className="h-4 w-4" />} title="Time Period">
            <div className="flex flex-col gap-3">
              <div className="text-sm font-semibold">
                {displayValue(timeData?.text)}
              </div>
              <TimelineBar
                fillPercent={timeData.fillPercent}
                start={timeData.start}
                end={timeData.end}
              />
            </div>
          </InfoCard>

          {/* Reproduction */}
          {hasReproData && (
            <InfoCard icon={<HeartPulse className="h-4 w-4" />} title="Reproduction">
              <dl className="flex flex-col">
                <ReproRow
                  label="Young Name"
                  value={repro.name_of_young ?? animal.young_name}
                />
                <ReproRow label="Group Name" value={animal.group_name} />
                <ReproRow label="Gestation" value={repro.gestation_period} />
                <ReproRow label="Litter Size" value={repro.average_litter_size} />
              </dl>
            </InfoCard>
          )}

          {/* Common names */}
          {animal.common_names && animal.common_names.length > 0 && (
            <InfoCard icon={<Languages className="h-4 w-4" />} title="Common Names">
              <p className="text-xs leading-relaxed text-muted-foreground">
                {animal.common_names.map((n) => n.name).join(", ")}
              </p>
            </InfoCard>
          )}
        </aside>
      </div>

      {/* Article sections */}
      <article className="mx-auto mt-14 max-w-3xl">
        {articleSections.map((section) => (
          <section
            key={section.id}
            id={section.id}
            className="mb-8 scroll-mt-24"
          >
            <h2 className="mb-3 border-b border-border pb-2 text-xl font-bold">
              {section.title}
            </h2>
            <p className="text-[0.95rem] leading-7 text-muted-foreground">
              {section.text}
            </p>
          </section>
        ))}
      </article>

      {/* FAQ */}
      <section className="mx-auto mt-10 max-w-4xl rounded-xl border border-border bg-card/40 p-6 sm:p-8">
        <h2 className="mb-6 text-xl font-bold">Frequently Asked Questions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {faqs.map((faq) => (
            <div
              key={faq.id}
              className="rounded-lg border border-border bg-background/60 p-4"
            >
              <h3 className="mb-2 text-sm font-semibold leading-snug">
                {faq.question}
              </h3>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {faq.answer}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Credits */}
      <section className="mt-10 border-t border-border py-6 text-center text-xs text-muted-foreground">
        <p>
          Data sourced from{" "}
          {animal.sources?.join(", ") ?? "Wikipedia, iNaturalist & Wikidata"}.
          {hasValue(animal.last_updated) && (
            <> Last updated {formatDate(animal.last_updated)}.</>
          )}
        </p>
      </section>
    </div>
  );
}

function InfoCard({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex items-center gap-2 text-[0.7rem] uppercase tracking-wide text-muted-foreground">
        <span className="shrink-0">{icon}</span>
        {title}
      </div>
      {children}
    </div>
  );
}

function ReproRow({ label, value }: { label: string; value?: string }) {
  if (!hasValue(value)) return null;
  return (
    <div className="flex justify-between border-b border-border py-2 last:border-0">
      <dt className="text-[0.7rem] uppercase tracking-wide text-muted-foreground">
        {label}
      </dt>
      <dd className="text-sm font-medium text-foreground">{value}</dd>
    </div>
  );
}

function SourceLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-primary/60 hover:text-primary"
    >
      {label}
      <ExternalLink className="h-3 w-3" aria-hidden="true" />
    </Link>
  );
}

function DistributionImage({ src, name }: { src: string; name: string }) {
  const [ok, setOk] = React.useState(true);
  if (!ok) return <WorldMap className="aspect-[2/1]" />;
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-background">
      <img
        src={src}
        alt={`${name} distribution map`}
        className="h-auto w-full"
        onError={() => setOk(false)}
      />
    </div>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function FetchingState({ name, onBack }: { name: string; onBack: () => void }) {
  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-20 text-center">
      <button
        type="button"
        onClick={onBack}
        className="mb-8 inline-flex items-center gap-2 rounded-md text-sm text-muted-foreground transition-colors hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to encyclopedia
      </button>
      <div className="mx-auto h-16 w-16 animate-spin rounded-full border-4 border-muted border-t-primary" />
      <h2 className="mt-6 text-xl font-semibold">Fetching {name}…</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        We&apos;re pulling the latest facts from Wikipedia and enriching them
        with AI. This usually takes 5–15 seconds — the page will update
        automatically.
      </p>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-8 h-4 w-40 animate-pulse rounded bg-muted" />
      <div className="mb-10 text-center">
        <div className="mx-auto h-12 w-64 animate-pulse rounded bg-muted" />
        <div className="mx-auto mt-3 h-5 w-48 animate-pulse rounded bg-muted" />
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[260px_1fr_260px]">
        <div className="hidden flex-col gap-4 lg:flex">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg border border-border bg-muted/40" />
          ))}
        </div>
        <div className="aspect-[16/10] animate-pulse rounded-2xl border border-border bg-muted/40" />
        <div className="hidden flex-col gap-4 lg:flex">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg border border-border bg-muted/40" />
          ))}
        </div>
      </div>
    </div>
  );
}
