/**
 * Utility functions for path generation and manipulation
 */

// Define the type for location points
export interface LocationPoint {
  lat: number;
  lon: number;
  name?: string;
}

// Define types for API request and response
interface PathRequestPayload {
  start_lat: number;
  start_lng: number;
  end_lat: number;
  end_lng: number;
}

interface PathResponse {
  path: [number, number][];
}

/**
 * Calculate path between two points using the API
 * @param startPoint - Starting location [lat, lon]
 * @param endPoint - Ending location [lat, lon]
 * @returns Promise containing the path as an array of [lat, lon] coordinates
 */
export async function calculatePathBetweenPoints(
  startPoint: LocationPoint,
  endPoint: LocationPoint
): Promise<[number, number][]> {
  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://calculatecampuspath-842151361761.us-central1.run.app";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        start_lat: startPoint.lat,
        start_lng: startPoint.lon,
        end_lat: endPoint.lat,
        end_lng: endPoint.lon,
      } as PathRequestPayload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Network response was not ok: ${response.status} - ${errorText}`
      );
    }

    const data = (await response.json()) as PathResponse;
    console.log("Path response:", data);
    return data.path;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to calculate path: ${error.message}`);
    } else {
      throw new Error("An unknown error occurred during path calculation");
    }
  }
}

/**
 * Generate a path through multiple points
 * @param points - Array of location points to visit in order
 * @returns Promise containing a complete path as an array of [lat, lon] coordinates
 */
export async function generatePath(
  points: LocationPoint[]
): Promise<[number, number][]> {
  if (points.length < 2) {
    throw new Error("At least two points are required to generate a path");
  }

  try {
    // Generate paths between consecutive points
    const pathPromises: Promise<[number, number][]>[] = [];

    for (let i = 0; i < points.length - 1; i++) {
      pathPromises.push(calculatePathBetweenPoints(points[i], points[i + 1]));
    }

    // Wait for all path calculations to complete
    const paths = await Promise.all(pathPromises);

    // Combine all paths into one continuous path
    // Note: We remove the last point of each path except the final one to avoid duplicates
    const combinedPath: [number, number][] = [];

    paths.forEach((path, index) => {
      // Add all points from this path
      if (index === paths.length - 1) {
        // For the last path, add all points
        combinedPath.push(...path);
      } else {
        // For other paths, add all points except the last one to avoid duplication
        combinedPath.push(...path.slice(0, -1));
      }
    });

    return combinedPath;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to generate complete path: ${error.message}`);
    } else {
      throw new Error("An unknown error occurred during path generation");
    }
  }
}
