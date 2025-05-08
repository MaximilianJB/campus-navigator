"use client";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from '@/components/ui/button';
import React, { useEffect, useState } from 'react';
import { Plus } from "lucide-react";
import Link from 'next/link';

interface MapItem {
    name: string;
    createdAt: string;
}

export function MapGrid() {
    const [maps, setMaps] = useState<MapItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetch('/api/maps')
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch maps');
                return res.json();
            })
            .then(data => setMaps(data.maps))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-16">
                <div className="w-12 h-12 border-4 border-t-primary border-gray-200 rounded-full animate-spin" />
            </div>
        );
    }

    if (error) {
        return <div className="text-red-500">Error: {error}</div>;
    }

    return (
        <div>
            <div className="animate-fade-in grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3">
                {maps.map((map) => (
                    <Card key={map.name}>
                        <CardHeader>
                            <CardTitle>{map.name}</CardTitle>
                            <CardDescription>
                                Created: {new Date(map.createdAt).toLocaleDateString()}
                            </CardDescription>
                        </CardHeader>
                    </Card>
                ))}
                <div className="flex items-center col-span-1 w-full">
                    <Link href="/map-upload" passHref legacyBehavior>
                        <Button
                            variant="outline"
                            size="lg"
                            className="w-full h-16 sm:aspect-square sm:h-full sm:w-auto shadow-none hover:scale-105 active:scale-95 rounded-lg flex items-center justify-center"
                        >
                            <Plus />
                        </Button>
                    </Link>
                </div>
            </div>
        </div>
    );
}