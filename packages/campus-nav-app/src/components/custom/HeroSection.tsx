"use client";

import { Button } from "../ui/button";
import Link from "next/link";

export function HeroSection() {
    return (
        <>
            <section className="mx-auto max-w-7xl mt-4 px-4 sm:px-6 lg:px-8">
                <div className="relative mb-8 overflow-hidden rounded-xl bg-gradient-to-br from-teal-50 via-white to-cyan-50 p-16 text-center shadow-sm">
                    {/* Grid overlay for map feel */}
                    <div
                        className="absolute inset-0 z-0 opacity-20"
                        style={{
                            backgroundImage:
                                'repeating-linear-gradient(90deg, #14b8a6 0px, #14b8a6 1px, transparent 1px, transparent 20px), ' +
                                'repeating-linear-gradient(0deg, #14b8a6 0px, #14b8a6 1px, transparent 1px, transparent 20px)',
                        }}
                    />

                    {/* Decorative map-like SVG background (visible above the gradient) */}
                    <div className="absolute inset-0 z-10 overflow-hidden">
                        <svg className="w-full h-full opacity-40" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" preserveAspectRatio="none">
                            <path className="path-anim" d="M0,100 C150,200 350,0 600,100" stroke="#14b8a6" fill="none" strokeWidth="2" />
                            <path className="path-anim" d="M0,300 C200,200 400,300 600,200" stroke="#2dd4bf" fill="none" strokeWidth="2" />
                        </svg>
                    </div>

                    {/* Text content */}
                    <div className="relative mt-8 flex flex-col gap-4 justify-center z-40">
                        <h1 className="relative text-5xl font-bold tracking-tight text-gray-900">Navigate your world</h1>
                        <p className="relative mt-2 text-lg text-gray-500">Upload GeoJSON to create custom maps and find the fastest routes.</p>
                    </div>

                    {/* CTA Buttons */}
                    <div className="relative mt-8 flex flex-col gap-4 sm:flex-row justify-center z-40">
                        <Link href="/navigator" passHref legacyBehavior>
                            <Button className="bg-teal-500 text-white transition-all hover:bg-teal-600 hover:scale-105 active:scale-95 w-full sm:w-auto mr-0 sm:mr-4">
                                Test with Gonzaga Map
                            </Button>
                        </Link>
                        <Link href="/map-upload" passHref legacyBehavior>
                            <Button
                                className="bg-white text-teal-600 border border-teal-500 transition-all hover:bg-teal-50 hover:scale-105 active:scale-95 w-full sm:w-auto"
                                variant="outline"
                            >
                                Upload Your Own Map
                            </Button>
                        </Link>
                    </div>

                </div>
            </section>
            {/* Animate SVG paths */}
            <style jsx>{`
              @keyframes dash {
                to { stroke-dashoffset: 0; }
              }
              .path-anim {
                stroke-dasharray: 300;
                stroke-dashoffset: 300;
                animation: dash 6s ease-out infinite;
              }
            `}</style>
        </>
    );
}