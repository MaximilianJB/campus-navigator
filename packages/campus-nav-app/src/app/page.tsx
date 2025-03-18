"use client";

import { useState, useMemo } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MapComponent from '@/components/custom/MapComponent';
import Navbar from '@/components/custom/Navbar';
import ManualEntryMode from '@/components/custom/ManualEntryMode';
import SchedulePlanningMode from '@/components/custom/SchedulePlanningMode';

export default function Home() {
  const [path, setPath] = useState<[number, number][] | null>(null); // Typed as array of [lat, lng] pairs
  const [cameraMode, setCameraMode] = useState<'aerial' | 'start'>('start');
  const [activeTab, setActiveTab] = useState<string>("manual");

  // Memoize the MapComponent to prevent re-renders when form inputs change
  const memoizedMap = useMemo(() => {
    // Only pass coordinates if path exists and is not empty
    return <MapComponent
      coordinates={path && path.length > 0 ? path : []}
      cameraMode={cameraMode}
    />;
  }, [path, cameraMode]); // Re-render when path or camera mode changes

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />

      <div className="flex flex-col items-center justify-center p-8 pb-20 gap-8 sm:p-12 flex-grow">
        <main className="grid grid-cols-1 sm:grid-cols-2 gap-8 items-start w-full">
          <div className="flex flex-col gap-6">
            <Tabs
              defaultValue="manual"
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="manual">Manual Test</TabsTrigger>
                <TabsTrigger value="schedule">Schedule Planning</TabsTrigger>
              </TabsList>
              <TabsContent
                value="manual"
                className="border border-gray-200 rounded-lg p-4 mt-2"
              >
                <ManualEntryMode
                  path={path}
                  setPath={setPath}
                  cameraMode={cameraMode}
                  setCameraMode={setCameraMode}
                />
              </TabsContent>
              <TabsContent
                value="schedule"
                className="border border-gray-200 rounded-lg p-4 mt-2"
              >
                <SchedulePlanningMode
                  path={path}
                  setPath={setPath}
                  cameraMode={cameraMode}
                  setCameraMode={setCameraMode}
                />
              </TabsContent>
            </Tabs>
          </div>
          {memoizedMap}
        </main>
      </div>
    </div>
  );
}