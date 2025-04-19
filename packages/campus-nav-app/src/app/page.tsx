import { Header } from "@/components/layout/Header";
import { HeroSection } from "@/components/custom/HeroSection";
import { MapGrid } from "@/components/custom/MapGrid";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col w-full">
      <Header />
      <main className="flex-1">
        <HeroSection />

        {/* Maps Section */}
        <section className="mx-auto max-w-7xl px-4 py-12 pt-0 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900">
              User Submitted Maps
            </h2>
            <p className="mt-2 text-lg text-gray-500">
              Try out custom GeoJSON maps from the community.
            </p>
          </div>

          <MapGrid />
        </section>
      </main>
    </div>
  );
}
