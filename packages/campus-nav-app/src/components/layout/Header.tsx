"use client";

import { Button } from "@/components/ui/button";
import { MapPinned, Menu, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export function Header() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen);
    };

    return (
        <header className="sticky top-0 z-50 w-full bg-white/80 backdrop-blur-sm transition-all">
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                <Link
                    href="/"
                    className="group flex items-center text-2xl font-bold tracking-tight"
                >
                    <div className="flex items-center gap-2 transition-colors group-hover:text-teal-500">
                        <MapPinned className="h-6 w-6 text-teal-500" />
                        <span className="font-bold text-foreground tracking-tight">
                            <span className="text-teal-500">Geo</span>Loom
                        </span>
                    </div>
                </Link>
                <div className="hidden sm:flex items-center gap-4">
                    <Button variant="ghost" asChild>
                        <Link href="/map-upload" className="font-medium">
                            Upload Map
                        </Link>
                    </Button>
                    <Button variant="ghost" asChild>
                        <Link href="/docs" className="font-medium">
                            Docs
                        </Link>
                    </Button>
                    <Button
                        asChild
                        className="bg-teal-500 text-white transition-all hover:bg-teal-600 hover:scale-105 active:scale-95"
                    >
                        <Link href="/navigator">Try the App</Link>
                    </Button>
                </div>
                <div className="sm:hidden">
                    <Button variant="ghost" size="icon" onClick={toggleMenu}>
                        {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                    </Button>
                </div>
            </div>
            {isMenuOpen && (
                <div className="sm:hidden bg-white w-full flex flex-col items-center gap-4 py-4 px-4 border-t border-gray-200">
                    <Button variant="ghost" asChild className="w-full justify-center">
                        <Link href="/map-upload" className="font-medium" onClick={toggleMenu}>
                            Upload Map
                        </Link>
                    </Button>
                    <Button variant="ghost" asChild className="w-full justify-center">
                        <Link href="/docs" className="font-medium" onClick={toggleMenu}>
                            Docs
                        </Link>
                    </Button>
                    <Button
                        asChild
                        className="bg-teal-500 text-white transition-all hover:bg-teal-600 hover:scale-105 active:scale-95 w-full justify-center"
                        onClick={toggleMenu}
                    >
                        <Link href="/navigator">Try the App</Link>
                    </Button>
                </div>
            )}
        </header>
    );
}