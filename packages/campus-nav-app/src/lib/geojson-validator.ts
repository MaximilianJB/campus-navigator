// Basic GeoJSON types (consider using a library like @types/geojson for full types)
export interface PointGeometry {
  type: 'Point';
  coordinates: [number, number];
}

export interface PolygonGeometry {
  type: 'Polygon';
  coordinates: [number, number][][]; // Array of linear rings
}

export interface LineStringGeometry {
  type: 'LineString';
  coordinates: [number, number][];
}

export interface Feature<
  G extends PointGeometry | PolygonGeometry | LineStringGeometry =
    | PointGeometry
    | PolygonGeometry
    | LineStringGeometry,
> {
  type: 'Feature';
  geometry: G;
  properties: Record<string, unknown>; // Use unknown instead of any
}

// We don't export FeatureCollection as the validator handles 'any' input

// Function to check if coordinates are finite numbers
const isValidCoordinate = (coord: unknown): coord is [number, number] =>
  Array.isArray(coord) && // Ensure it's an array first
  coord.length === 2 &&
  Number.isFinite(coord[0]) &&
  Number.isFinite(coord[1]);

// Function to check if a ring is linear (basic check - doesn't check self-intersection)
const isLinearRing = (ring: unknown): ring is [number, number][] =>
  Array.isArray(ring) &&
  ring.length >= 4 && // Must have at least 4 points (first and last are the same)
  isValidCoordinate(ring[0]) &&
  isValidCoordinate(ring[ring.length - 1]) &&
  ring[0][0] === ring[ring.length - 1][0] &&
  ring[0][1] === ring[ring.length - 1][1] &&
  ring.every(isValidCoordinate);

// Validation function
export const validateGeoJSON = (data: unknown, fileSize: number): string[] => {
  const errs: string[] = [];
  const MAX_FILE_SIZE_MB = 10;
  const MAX_FEATURES = 500;

  // File Size Check
  if (fileSize / (1024 * 1024) > MAX_FILE_SIZE_MB) {
    errs.push(`File size exceeds ${MAX_FILE_SIZE_MB} MB limit.`);
  }

  // Top-level structure checks
  if (typeof data !== 'object' || data === null) {
    errs.push('Invalid JSON: Root must be an object.');
    return errs; // Stop further checks if not an object
  }

  // Type assertion for easier access, assuming basic object structure
  const geoJsonData = data as Record<string, unknown>;

  if (geoJsonData?.type !== 'FeatureCollection') {
    errs.push('Invalid GeoJSON: Top-level "type" must be "FeatureCollection".');
  }
  if (!Array.isArray(geoJsonData.features)) {
    errs.push('Invalid GeoJSON: Missing or invalid "features" array.');
    return errs; // Stop if features array is missing/invalid
  }
  if (geoJsonData.features.length === 0) {
    errs.push('Invalid GeoJSON: Features array cannot be empty.');
  }

  // Feature count check
  if (geoJsonData.features.length > MAX_FEATURES) {
    errs.push(`Feature count exceeds ${MAX_FEATURES} limit.`);
  }

  // Feature-level checks
  let hasPolygon = false;
  let hasPoint = false;
  let hasLineString = false;
  const pointCoordinates = new Set<string>();

  // Use type assertion after initial checks pass
  const features = geoJsonData.features as Feature[];

  for (const feature of features) {
    if (feature?.type !== 'Feature') {
      errs.push(
        'Invalid Feature: Each item in "features" must have type "Feature".'
      );
      continue;
    }
    if (!feature.geometry) {
      errs.push('Invalid Feature: Missing "geometry" object.');
      continue;
    }

    const geometryType = feature.geometry.type;

    if (geometryType === 'Polygon') {
      hasPolygon = true;
      const polygonFeature = feature as Feature<PolygonGeometry>;
      // Basic Polygon Checks
      //   const props = polygonFeature.properties as Record<string, unknown>;
      //   if (!props?.name || typeof props.name !== 'string') {
      //     console.log(props);
      //     errs.push(
      //       `Invalid Polygon Feature: Missing or empty "properties.name".`
      //     );
      //   }
      // Check coordinates structure
      if (
        !Array.isArray(polygonFeature.geometry.coordinates) ||
        polygonFeature.geometry.coordinates.length === 0
      ) {
        errs.push(
          `Invalid Polygon Geometry: "coordinates" must be a non-empty array of rings.`
        );
      } else {
        // Basic linear ring check (doesn't check self-intersection)
        if (!isLinearRing(polygonFeature.geometry.coordinates[0])) {
          errs.push(
            `Invalid Polygon Geometry: Outer ring must be a valid LinearRing (>=4 points, closed, finite coordinates).`
          );
        }
        // TODO: Add area > 0 check (requires geometry library)
        // TODO: Add self-intersection check (requires geometry library)
      }
    } else if (geometryType === 'Point') {
      hasPoint = true;
      const pointFeature = feature as Feature<PointGeometry>;
      // Basic Point Checks
      if (!isValidCoordinate(pointFeature.geometry.coordinates)) {
        errs.push(
          `Invalid Point Geometry: Coordinates must be [longitude, latitude] with finite numbers.`
        );
      } else {
        // Check for duplicate points
        const coordString = pointFeature.geometry.coordinates.join(',');
        if (pointCoordinates.has(coordString)) {
          errs.push(`Duplicate Point coordinate found: [${coordString}].`);
        }
        pointCoordinates.add(coordString);
        // TODO: Add point-in-polygon check (requires geometry library & polygon data)
      }
    } else if (geometryType === 'LineString') {
      hasLineString = true;
      const lineFeature = feature as Feature<LineStringGeometry>;
      // Basic LineString Checks
      if (
        !Array.isArray(lineFeature.geometry.coordinates) ||
        lineFeature.geometry.coordinates.length < 2
      ) {
        errs.push(
          `Invalid LineString Geometry: "coordinates" must be an array of at least 2 points.`
        );
      } else {
        lineFeature.geometry.coordinates.forEach((coord, idx) => {
          if (!isValidCoordinate(coord)) {
            errs.push(
              `Invalid LineString Geometry: Coordinate at index ${idx} is invalid.`
            );
          }
        });
      }
    } else {
      errs.push(
        `Unsupported Feature Type: "${geometryType}". Only "Polygon", "Point", and "LineString" are supported.`
      );
    }
  }

  // Check for presence of required feature types
  if (!hasPolygon) {
    errs.push('Validation Error: At least one Polygon feature is required.');
  }
  if (!hasPoint) {
    errs.push('Validation Error: At least one Point feature is required.');
  }
  if (!hasLineString) {
    errs.push('Validation Error: At least one LineString feature is required.');
  }

  return errs;
};
