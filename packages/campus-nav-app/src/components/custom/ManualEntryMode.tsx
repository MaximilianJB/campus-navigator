"use client";

import { useState } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import GetLocationButton from '@/components/custom/GetLocationButton';

interface ManualEntryModeProps {
  path: [number, number][] | null;
  setPath: (path: [number, number][] | null) => void;
  cameraMode: 'aerial' | 'start';
  setCameraMode: (mode: 'aerial' | 'start') => void;
}

export default function ManualEntryMode({ path, setPath, cameraMode, setCameraMode }: ManualEntryModeProps) {
  const [startLat, setStartLat] = useState('');
  const [startLng, setStartLng] = useState('');
  const [endLat, setEndLat] = useState('');
  const [endLng, setEndLng] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://calculatecampuspath-842151361761.us-central1.run.app';

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!startLat || !startLng || !endLat || !endLng) {
      setError('All fields are required');
      return;
    }

    const startLatNum = parseFloat(startLat);
    const startLngNum = parseFloat(startLng);
    const endLatNum = parseFloat(endLat);
    const endLngNum = parseFloat(endLng);

    if (isNaN(startLatNum) || isNaN(startLngNum) || isNaN(endLatNum) || isNaN(endLngNum)) {
      setError('Please enter valid numbers');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_lat: startLatNum,
          start_lng: startLngNum,
          end_lat: endLatNum,
          end_lng: endLngNum,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Network response was not ok: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      setPath(data.path);
      // Set default camera view to start when path is first calculated
      setCameraMode('start');
    } catch (err) {
      if (err instanceof Error) {
        // Enhanced error message to help debug CORS or server issues
        setError(`Failed to fetch path: ${err.message}${err.message.includes('CORS') ? ' (Check API CORS settings)' : ''}`);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDefaultValueFill = () => {
    setEndLat('47.66599');
    setEndLng('-117.40038');
    setStartLat('47.66840');
    setStartLng('-117.40785');
  };

  return (
    <div className='flex flex-col flex-1 gap-6'>
      <div className='grid grid-cols-2 gap-4 w-full'>
        <Button variant="outline" className="w-full" onClick={handleDefaultValueFill}>
          Fill with default values
        </Button>
        <GetLocationButton onLocationObtained={(lat, long) => {
          setStartLat(lat.toString());
          setStartLng(long.toString());
        }} />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="startLat" className="block text-sm font-medium">Start Latitude</label>
            <Input
              id="startLat"
              type="number"
              step="any"
              value={startLat}
              onChange={(e) => setStartLat(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="startLng" className="block text-sm font-medium">Start Longitude</label>
            <Input
              id="startLng"
              type="number"
              step="any"
              value={startLng}
              onChange={(e) => setStartLng(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="endLat" className="block text-sm font-medium">End Latitude</label>
            <Input
              id="endLat"
              type="number"
              step="any"
              value={endLat}
              onChange={(e) => setEndLat(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="endLng" className="block text-sm font-medium">End Longitude</label>
            <Input
              id="endLng"
              type="number"
              step="any"
              value={endLng}
              onChange={(e) => setEndLng(e.target.value)}
            />
          </div>
        </div>
        <Button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Calculate Path'}
        </Button>
      </form>

      {error && <div className="text-red-500 mt-4">{error}</div>}

      {/* Success block with camera controls */}
      {path && path.length > 0 && (
        <div className="bg-green-100 border border-green-200 rounded-lg p-4 mt-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-green-700 font-medium">Path Calculated!</h3>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <div className="flex gap-2">
              <Button
                size="sm"
                variant={cameraMode === 'aerial' ? 'default' : 'outline'}
                onClick={() => setCameraMode('aerial')}
                className="text-xs py-1 h-auto"
              >
                Aerial View
              </Button>
              <Button
                size="sm"
                variant={cameraMode === 'start' ? 'default' : 'outline'}
                onClick={() => setCameraMode('start')}
                className="text-xs py-1 h-auto"
              >
                Start View
              </Button>
            </div>
          </div>

          <div className="mt-4">
            <Collapsible className="w-full max-w-md">
              <CollapsibleTrigger className="text-sm text-green-600 underline cursor-pointer">
                Toggle View Path Data
              </CollapsibleTrigger>
              <CollapsibleContent>
                <pre className="bg-white p-4 rounded mt-2 text-xs overflow-auto max-h-40">
                  {JSON.stringify(path, null, 2)}
                </pre>
              </CollapsibleContent>
            </Collapsible>
          </div>
        </div>
      )}
    </div>
  );
}
