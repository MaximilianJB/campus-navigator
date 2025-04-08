import path from 'path';
import { promises as fsPromises } from 'fs';

export interface BuildingEntrance {
  name: string;
  lat: number;
  lon: number;
}

export interface Building {
  name: string;
  entrances: BuildingEntrance[];
}

/**
 * Processes the building_entrances_db.csv file and returns a structured JSON
 * with buildings as individual entries and their entrances nested within.
 */
export async function getBuildingEntrances(): Promise<Building[]> {
  try {
    const filePath = path.join(process.cwd(), 'public', 'building_entrances_db.csv');
    const fileContent = await fsPromises.readFile(filePath, 'utf8');
    
    const lines = fileContent.split('\n').filter(line => line.trim() !== '');
    // Skip the header line
    const dataLines = lines.slice(1);
    
    const buildingsMap = new Map<string, Building>();
    
    dataLines.forEach(line => {
      const [building, entrance, latStr, lonStr] = line.split(',');
      
      // Skip invalid lines
      if (!building || !latStr || !lonStr) return;
      
      const lat = parseFloat(latStr);
      const lon = parseFloat(lonStr);
      
      // Skip invalid coordinates
      if (isNaN(lat) || isNaN(lon)) return;
      
      if (!buildingsMap.has(building)) {
        buildingsMap.set(building, {
          name: building,
          entrances: []
        });
      }
      
      const entranceName = entrance || 'Main'; // Default to 'Main' if no entrance name provided
      
      buildingsMap.get(building)!.entrances.push({
        name: entranceName,
        lat,
        lon
      });
    });
    
    return Array.from(buildingsMap.values());
  } catch (error) {
    console.error('Error processing building entrances:', error);
    return [];
  }
}

/**
 * Returns the building entrances data as a pre-processed JSON object.
 * This version works on the client-side by importing a JSON file.
 */
export function getBuildingEntrancesClientSide(): Building[] {
  try {
    // In a real implementation, we'd import a pre-processed JSON file
    // For now, we'll return an empty array and let the component fetch the data
    return [];
  } catch (error) {
    console.error('Error getting building entrances on client side:', error);
    return [];
  }
}
