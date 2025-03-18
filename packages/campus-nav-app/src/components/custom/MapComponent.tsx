import type React from "react";
import { useCallback, useEffect, useMemo, useRef, memo } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import simplify from "simplify-js"

// Define the props interface for the component
interface MapComponentProps {
	coordinates: [number, number][]; // 2D array of [latitude, longitude]
	cameraMode: 'aerial' | 'start';
	onBoundsCalculated?: (hasBounds: boolean) => void;
}

const MapComponent: React.FC<MapComponentProps> = memo(({ coordinates, cameraMode, onBoundsCalculated }) => {
	// Type the refs for the map container and map instance
	const mapContainer = useRef<HTMLDivElement | null>(null);
	const map = useRef<mapboxgl.Map | null>(null);

	// Simplify the coordinates - memoize this calculation
	const smoothedCoordinatesArray = useMemo(() => {
		const tolerance = 0.0001; // Adjust tolerance as needed
		const highQuality = true; // Set to true for more accurate results
		const pointCoordinates = coordinates.map(coord => ({ x: coord[0], y: coord[1] }));
		const smoothedCoordinates = simplify(pointCoordinates, tolerance, highQuality);
		return smoothedCoordinates.map(point => [point.x, point.y] as [number, number]);
	}, [coordinates]);

	// Convert coordinates to GeoJSON format
	const geojson = useMemo(
		() => ({
			type: "Feature" as const,
			properties: {},
			geometry: {
				type: "LineString" as const,
				coordinates: smoothedCoordinatesArray.map(([lat, lon]) => [lon, lat]), // Swap to [longitude, latitude]
			},
		}),
		[smoothedCoordinatesArray],
	);

	// Utility functions for bearing calculation
	const toRadians = useCallback((deg: number) => (deg * Math.PI) / 180, []);
	const toDegrees = useCallback((rad: number) => (rad * 180) / Math.PI, []);

	const calculateBearing = useCallback(
		(start: [number, number], end: [number, number]) => {
			const [lat1, lon1] = start;
			const [lat2, lon2] = end;
			const φ1 = toRadians(lat1);
			const φ2 = toRadians(lat2);
			const Δλ = toRadians(lon2 - lon1);
			const y = Math.sin(Δλ) * Math.cos(φ2);
			const x =
				Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
			const bearing = toDegrees(Math.atan2(y, x));
			return bearing;
		},
		[toRadians, toDegrees]
	);

	// Calculate bounds from coordinates
	const calculateBounds = useCallback((coords: [number, number][]): mapboxgl.LngLatBounds | null => {
		if (coords.length === 0) return null;

		const bounds = new mapboxgl.LngLatBounds();

		// Add all points to the bounds
		coords.forEach(([lat, lng]) => {
			bounds.extend([lng, lat]);
		});

		return bounds;
	}, []);

	// Camera control functions
	const setAerialView = useCallback(() => {
		if (!map.current || coordinates.length === 0) return;

		// Calculate bounds for all coordinates
		const bounds = calculateBounds(coordinates);
		if (!bounds) return;

		// Fit to bounds with a top-down view
		map.current.fitBounds(bounds, {
			padding: 50,
			pitch: 0, // Top-down view
			bearing: 0, // North-oriented
			maxZoom: 16, // Limit max zoom to ensure we can see enough context
			duration: 1500 // Animation duration in ms
		});
	}, [coordinates, calculateBounds]);

	const setStartView = useCallback(() => {
		if (!map.current || coordinates.length === 0) return;

		const start = coordinates[0];
		const end = coordinates[coordinates.length - 1];
		const bearing = calculateBearing(start, end);

		// Focus on the start with a tilted view
		map.current.flyTo({
			center: [start[1], start[0]], // Start point in [longitude, latitude]
			zoom: 17, // High zoom level for close-up view
			pitch: 45, // 45-degree tilt
			bearing: bearing, // Points towards the end
			speed: 1, // Animation speed
			curve: 1, // Smooth animation curve
			duration: 1500 // Animation duration in ms
		});
	}, [coordinates, calculateBearing]);

	// Initialize the map only once when the component mounts
	useEffect(() => {
		if (!mapContainer.current) return; // Guard against null ref
		if (map.current) return; // Skip if map already exists

		// Set Mapbox access token
		mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || ""; // Ensure you have the token in your .env.local file

		// Create the map instance
		map.current = new mapboxgl.Map({
			container: mapContainer.current,
			style: process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL || "", // Ensure you have the style URL in your .env.local file
			center: [-117.404, 47.66626] as [number, number],
			zoom: 10,
		});

		// When the map loads, add the path and adjust the view if coordinates are available
		map.current.on("load", () => {
			if (!map.current) return; // Guard against null map

			// Initially add the GeoJSON source even with empty coordinates
			map.current.addSource("route", {
				type: "geojson",
				data: {
					type: "Feature",
					properties: {},
					geometry: {
						type: "LineString",
						coordinates: [],
					},
				},
			});

			// Add a layer to display the path as a line
			map.current.addLayer({
				id: "route",
				type: "line",
				source: "route",
				layout: {
					"line-join": "round",
					"line-cap": "round",
				},
				paint: {
					"line-color": "#B33C86",
					"line-width": 3,
				},
			});
		});

		// Cleanup: remove the map when the component unmounts
		return () => {
			if (map.current) {
				map.current.remove();
				map.current = null;
			}
		};
	}, []); // Empty dependency array ensures this effect runs only once

	// Update the map when coordinates change and the map is ready
	useEffect(() => {
		if (!map.current || !map.current.loaded()) return;

		const source = map.current.getSource("route");
		if (!source || !("setData" in source)) return;

		// Update the GeoJSON source with new coordinates
		(source as mapboxgl.GeoJSONSource).setData(geojson);

		// Only update view if there are coordinates
		if (coordinates.length > 0) {
			// Use the current camera mode to determine how to position the camera
			if (cameraMode === 'aerial') {
				setAerialView();
			} else {
				setStartView();
			}
		}

		// Notify parent component about bounds calculation
		if (onBoundsCalculated) {
			const bounds = calculateBounds(coordinates);
			onBoundsCalculated(bounds !== null);
		}
	}, [coordinates, geojson, cameraMode, setAerialView, setStartView, onBoundsCalculated, calculateBounds]); // Fixed by adding calculateBounds

	// Render a square map container
	return (
		<div
			ref={mapContainer}
			style={{
				width: "100%",
				paddingBottom: "100%", // This ensures a square aspect ratio
				position: "relative",
				borderRadius: "10px",
			}}
		>
			<div
				style={{
					position: "absolute",
					top: 0,
					left: 0,
					right: 0,
					bottom: 0,
				}}
			/>
		</div>
	);
});

// Add display name for debugging
MapComponent.displayName = "MapComponent";

export default MapComponent;
