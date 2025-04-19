"use client";

import { useState, useMemo, useCallback } from 'react';
import MapComponent from '@/components/custom/MapComponent';
import RoutePlanningMode, { RouteEntrance } from '@/components/custom/RoutePlanningModule'; // Renamed import
import { Toaster } from "@/components/ui/toaster" // Optional: For potential future notifications
import { useToast } from "@/hooks/use-toast" // Optional: For potential future notifications


export default function NavigatorPage() {
    const [path, setPath] = useState<[number, number][] | null>(null);
    const [cameraMode, setCameraMode] = useState<'aerial' | 'start'>('start');
    const [entrances, setEntrances] = useState<RouteEntrance[]>([]); // Renamed interface
    const { toast } = useToast(); // Optional: For potential future notifications

    // Handle entrances change from RoutePlanningMode
    const handleEntrancesChange = useCallback((newEntrances: RouteEntrance[]) => {
        setEntrances(newEntrances);
        // Clear the path when entrances change significantly (e.g., pins added/removed)
        // You might want more sophisticated logic here depending on UX needs
        if (path) {
            setPath(null);
        }
    }, [path]); // Dependency on path to allow clearing it

    // Handle path generated from the route planner
    const handlePathGenerated = useCallback((generatedPath: [number, number][]) => {
        setPath(generatedPath);
        setCameraMode('aerial'); // Switch to aerial view to see the entire path
        // Optional: Add success feedback
        toast({
            title: "Route Generated",
            description: "The optimal route between your pins is now displayed.",
            variant: "default", // Use 'default' or 'success' if you add a success variant
        });
    }, [toast]);

    // Memoize the MapComponent to prevent re-renders unless necessary props change
    const memoizedMap = useMemo(() => {
        return <MapComponent
            coordinates={path ?? []} // Use nullish coalescing for cleaner empty array handling
            cameraMode={cameraMode}
            entrances={entrances} // Pass the updated entrances (pins)
        />;
    }, [path, cameraMode, entrances]); // Re-render only when these change

    return (
        // Main container with flex layout, header fixed at top
        <div className="flex flex-col h-screen">
            <main className='flex flex-1 overflow-hidden'> {/* Flex container for sidebar and map */}
                {/* Sidebar: Fixed width, scrollable content */}
                <div className='w-full max-w-sm lg:max-w-md xl:max-w-lg border-r border-border bg-background flex flex-col'>
                    <RoutePlanningMode
                        onEntrancesChange={handleEntrancesChange}
                        onPathGenerated={handlePathGenerated}
                        setCameraMode={setCameraMode} // Pass setter
                        cameraMode={cameraMode}        // Pass current mode
                    />
                </div>


                <div className='flex-1 relative p-4 max-h-fit h-screen'>
                    {memoizedMap}
                </div>
            </main>
            <Toaster />
        </div>
    );
}