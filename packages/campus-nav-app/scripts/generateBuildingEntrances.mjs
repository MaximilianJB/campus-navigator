// Script to generate building entrances JSON from CSV
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get the directory name using ES modules approach
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to CSV and output JSON
const csvPath = path.join(__dirname, '..', 'public', 'building_entrances_db.csv');
const jsonOutputPath = path.join(__dirname, '..', 'public', 'building_entrances.json');

function processCSV() {
  try {
    const fileContent = fs.readFileSync(csvPath, 'utf8');
    const lines = fileContent.split('\n').filter(line => line.trim() !== '');
    // Skip the header line
    const dataLines = lines.slice(1);
    
    const buildingsMap = new Map();
    
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
      
      buildingsMap.get(building).entrances.push({
        name: entranceName,
        lat,
        lon
      });
    });
    
    const buildingsArray = Array.from(buildingsMap.values());
    fs.writeFileSync(jsonOutputPath, JSON.stringify(buildingsArray, null, 2));
    console.log(`Successfully generated JSON at ${jsonOutputPath}`);
  } catch (error) {
    console.error('Error processing building entrances:', error);
  }
}

processCSV();
