"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface AnimalImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src?: string;
  alt: string;
  /** Fallback initials/emoji shown while loading or when the image fails. */
  fallbackLabel?: string;
}

/**
 * Image with graceful fallback: shows a neutral placeholder with the
 * animal's initial while loading and if the remote image fails to load
 * (Wikipedia hot-linking can be flaky).
 */
export function AnimalImage({
  src,
  alt,
  fallbackLabel,
  className,
  ...props
}: AnimalImageProps) {
  const [status, setStatus] = React.useState<"loading" | "loaded" | "error">(
    src ? "loading" : "error",
  );

  React.useEffect(() => {
    setStatus(src ? "loading" : "error");
  }, [src]);

  const initial = (fallbackLabel ?? alt ?? "?").charAt(0).toUpperCase();

  return (
    <div className={cn("relative overflow-hidden bg-muted", className)}>
      {status !== "error" && src ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setStatus("loaded")}
          onError={() => setStatus("error")}
          className={cn(
            "h-full w-full object-cover transition-opacity duration-300",
            status === "loaded" ? "opacity-100" : "opacity-0",
          )}
          {...props}
        />
      ) : null}

      {status !== "loaded" && (
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-muted to-muted/60">
          <span className="font-serif text-3xl italic text-muted-foreground">
            {initial}
          </span>
        </div>
      )}
    </div>
  );
}
