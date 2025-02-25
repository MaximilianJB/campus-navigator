"use client";

import { useState } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

export default function Home() {
  const [startLat, setStartLat] = useState('');
  const [startLng, setStartLng] = useState('');
  const [endLat, setEndLat] = useState('');
  const [endLng, setEndLng] = useState('');
  const [path, setPath] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      const response = await fetch('https://calculatecampuspath-842151361761.us-central1.run.app', {
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
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setPath(data.path);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDefaultValueFill = () => {
    setStartLat('47.6625');
    setStartLng('-117.4090');
    setEndLat('47.6700');
    setEndLng('-117.3970');
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="flex flex-col gap-8 items-center">
        <h1 className="text-3xl font-bold">Campus Navigator</h1>
        <Button variant='outline' className='w-full' onClick={handleDefaultValueFill}>
          Fill with default values
        </Button>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-md">
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

        {path && (
          <Collapsible className="mt-4 w-full">
            <CollapsibleTrigger className="w-full">
              View Path
            </CollapsibleTrigger>
            <CollapsibleContent>
              <pre className="bg-gray-100 p-4 rounded mt-2">{JSON.stringify(path, null, 2)}</pre>
            </CollapsibleContent>
          </Collapsible>
        )}
      </main>
    </div >
  );
}