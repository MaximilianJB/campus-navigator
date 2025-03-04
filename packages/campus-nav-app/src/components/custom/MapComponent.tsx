import React, { useEffect, useMemo, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Define the props interface for the component
interface MapComponentProps {
    coordinates: [number, number][]; // 2D array of [latitude, longitude]
}

const MapComponent: React.FC<MapComponentProps> = ({ coordinates }) => {
    // Type the refs for the map container and map instance
    const mapContainer = useRef<HTMLDivElement | null>(null);
    const map = useRef<mapboxgl.Map | null>(null);

    // Convert coordinates to GeoJSON format
    const geojson = useMemo(() => ({
        type: "Feature" as const,
        properties: {},
        geometry: {
            type: 'LineString' as const,
            coordinates: coordinates.map(([lat, lon]) => [lon, lat]), // Swap to [longitude, latitude]
        },
    }), [coordinates]);

    // Function to calculate bounds from coordinates
    const getBounds = (coords: [number, number][]): [[number, number], [number, number]] => {
        const latitudes = coords.map(coord => coord[0]);
        const longitudes = coords.map(coord => coord[1]);
        const minLat = Math.min(...latitudes);
        const maxLat = Math.max(...latitudes);
        const minLon = Math.min(...longitudes);
        const maxLon = Math.max(...longitudes);
        return [[minLon, minLat], [maxLon, maxLat]];
    };

    // Utility functions for bearing calculation
    const toRadians = (deg: number) => deg * Math.PI / 180;
    const toDegrees = (rad: number) => rad * 180 / Math.PI;

    const calculateBearing = (start: [number, number], end: [number, number]): number => {
        const [lat1, lon1] = start;
        const [lat2, lon2] = end;
        const φ1 = toRadians(lat1);
        const φ2 = toRadians(lat2);
        const Δλ = toRadians(lon2 - lon1);
        const y = Math.sin(Δλ) * Math.cos(φ2);
        const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
        const bearing = toDegrees(Math.atan2(y, x));
        return bearing;
    };

    // Initialize the map when the component mounts
    useEffect(() => {
        if (!mapContainer.current) return; // Guard against null ref

        // Set Mapbox access token
        mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || ''; // Ensure you have the token in your .env.local file

        // Create the map instance
        map.current = new mapboxgl.Map({
            container: mapContainer.current,
            style: process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL || '', // Ensure you have the style URL in your .env.local file
            center: [-117.40400, 47.66626] as [number, number],
            zoom: 10,
        });

        //47.66626, 117.40400

        // When the map loads, add the path and adjust the view
        map.current.on('load', () => {
            if (!map.current) return; // Guard against null map

            if (coordinates.length > 0) {
                // Add the GeoJSON source for the path
                map.current.addSource('route', {
                    type: 'geojson',
                    data: geojson,
                });

                // Add a layer to display the path as a line
                map.current.addLayer({
                    id: 'route',
                    type: 'line',
                    source: 'route',
                    layout: {
                        'line-join': 'round',
                        'line-cap': 'round',
                    },
                    paint: {
                        'line-color': '#B33C86',
                        'line-width': 3,
                    },
                });

                // Calculate bounds and bearing
                // const bounds = getBounds(coordinates);
                const start = coordinates[0];
                const end = coordinates[coordinates.length - 1];
                const bearing = calculateBearing(start, end);

                // Fit bounds with pitch and bearing
                map.current.flyTo({
                    center: [start[1], start[0]], // Start point in [longitude, latitude]
                    zoom: 17, // High zoom level for close-up view
                    pitch: 45, // 45-degree tilt
                    bearing: bearing, // Points towards the end
                    speed: 1, // Animation speed
                    curve: 1, // Smooth animation curve
                });
            }
        });

        // Cleanup: remove the map when the component unmounts
        return () => {
            if (map.current) {
                map.current.remove();
            }
        };
    }, [coordinates, geojson]);

    // Update the map when coordinates change
    useEffect(() => {
        if (map.current && map.current.getSource('route')) {
            if (coordinates.length > 0) {
                // Update the GeoJSON source with new coordinates
                const source = map.current.getSource('route');
                if (source && 'setData' in source) {
                    (source as mapboxgl.GeoJSONSource).setData(geojson);
                }
                // Recalculate and fit to new bounds
                const bounds = getBounds(coordinates);
                map.current.fitBounds(bounds, { padding: 20 });
            } else {
                // Remove the layer and source if coordinates are empty
                if (map.current.getLayer('route')) {
                    map.current.removeLayer('route');
                }
                if (map.current.getSource('route')) {
                    map.current.removeSource('route');
                }
            }
        }
    }, [coordinates, geojson]); // Runs whenever coordinates prop changes

    // Render a square map container
    return (
        <div
            ref={mapContainer}
            style={{
                width: '100%',
                paddingBottom: '100%', // This ensures a square aspect ratio
                position: 'relative',
                borderRadius: '10px'
            }}
        >
            <div
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                }}
            />
        </div>
    );
};

export default MapComponent;