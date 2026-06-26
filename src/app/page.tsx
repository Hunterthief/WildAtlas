import { Suspense } from "react";
import { WildAtlasApp } from "@/components/wildatlas/wildatlas-app";

export default function Home() {
  return (
    <Suspense fallback={null}>
      <WildAtlasApp />
    </Suspense>
  );
}
