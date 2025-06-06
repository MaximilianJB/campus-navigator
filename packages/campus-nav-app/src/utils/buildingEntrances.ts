const entrancesData = `Name,Lat,Lon
Kennedy,47.6686,-117.4081
Tilford North,47.6679,-117.4086
Tilford South,47.6675,-117.4088
Dussault A North,47.6672,-117.4083
Dussault A West,47.6671,-117.4087
Dussault B North,47.6668,-117.4082
Dussault B West,47.6667,-117.4086
Dussault B South,47.6667,-117.4083
Dussault C West,47.6664,-117.4086
Dussault C South,47.6663,-117.4083
Journalism & Broadcast,47.6686,-117.4074
Music Annex North,47.6683,-117.4076
Music Annex East,47.6682,-117.4073
Music Annex South,47.668,-117.4075
Human Physiology,47.6679,-117.4076
Burch A East,47.6693,-117.407
Burch A South,47.6692,-117.4067
Burch B,47.669,-117.4069
Burch C,47.669,-117.4066
Music Building,47.6686,-117.4067
Music Hall North,47.6682,-117.4063
Music Hall South,47.6679,-117.4063
Myrtle Woldson Center,47.6672,-117.4067
Jundt Center,47.6665,-117.407
Dooley,47.6693,-117.4055
Jepson West,47.6673,-117.4056
Jepson East,47.6673,-117.405
Jepson South,47.6669,-117.405
Robinson House,47.6686,-117.4044
St. Aloysius,47.6682,-117.4042
Humanities Building West,47.6672,-117.4041
Humanities Building East,47.6672,-117.4038
Cataldo,47.6686,-117.4036
College Hall NorthWest,47.6682,-117.4031
College Hall West,47.6681,-117.4034
College Hall SouthWest 1,47.668,-117.4032
College Hall SouthWest 2,47.668,-117.4029
College Hall NorthEast,47.6682,-117.4019
College Hall SouthEast,47.668,-117.4019
Hughes Hall,47.667,-117.403
Herek West,47.6668,-117.4027
Herek East,47.6668,-117.4018
Herek South,47.6665,-117.402
Paccar East,47.6664,-117.4019
Paccar North,47.6664,-117.4025
Paccar South,47.6662,-117.4025
Bollier East,47.6663,-117.4028
Bollier South ,47.6662,-117.4038
Bollier North,47.6664,-117.4037
Bollier West,47.6664,-117.404
Crimont,47.6702,-117.4017
Corkery A West ,47.6702,-117.4011
Corkery A East,47.6702,-117.4007
Corkery B North,47.6703,-117.4003
Corkery B South,47.67,-117.4003
Corkery C West,47.6699,-117.4006
Corkery C East,47.6699,-117.4001
Dillon West,47.6692,-117.4012
Dillon South,47.6691,-117.4008
Goller South ,47.6691,-117.4004
Goller East,47.6692,-117.4
Alliance,47.6686,-117.4002
DeSmet East,47.6678,-117.401
Desmet West,47.6678,-117.4012
Crosby,47.6674,-117.4014
Foley,47.6666,-117.4008
RFC North,47.6658,-117.4006
RFC South,47.6647,-117.4006
Kennel,47.6658,-117.3993
Welch East,47.6678,-117.4002
Welch South,47.6676,-117.4
Hemmingson NorthWest,47.6672,-117.3999
Hemmingson SouthWest,47.6669,-117.3997
Hemmingson NorthEast,47.6672,-117.399
Hemmingson SouthEast,47.667,-117.399
Lincoln,47.6686,-117.3994
Health Center,47.6694,-117.3994
Rosauer Center North,47.6683,-117.3991
Rosauer Center South,47.668,-117.3992
Student Wellness Center,47.6678,-117.3984
Sodexo,47.6675,-117.3984
Twohy,47.6687,-117.3979
Madonna West,47.6669,-117.3977
Madonna North,47.6672,-117.3973
Madonna South,47.6665,-117.3973
Madonna Back Door,47.6669,-117.3973
Cathrine Monica North,47.6663,-117.3972
Cathrine Monica East,47.6659,-117.3969
Cathrine Monica West,47.6659,-117.3976
Law School,47.6635,-117.4004`;

export interface BuildingEntrance {
  fullName: string;      // Full entry name as it appears in CSV
  building: string;      // Extracted building name
  direction?: string;    // Cardinal direction if available
  lat: number;
  lon: number;
}

export interface GroupedEntrances {
  [key: string]: BuildingEntrance[];  // Grouped by building name
}

/**
 * Parses the full entrance name to extract building name and direction
 */
function parseEntranceName(fullName: string): { building: string, direction?: string } {
  // Common suffixes that indicate directions
  const directionKeywords = [
    'North', 'South', 'East', 'West', 
    'NorthWest', 'NorthEast', 'SouthWest', 'SouthEast',
    'A North', 'A South', 'A East', 'A West',
    'B North', 'B South', 'B East', 'B West',
    'C North', 'C South', 'C East', 'C West'
  ];

  // Check if the name contains any direction keywords
  for (const direction of directionKeywords) {
    if (fullName.endsWith(direction)) {
      // Extract the building name (everything before the direction)
      const building = fullName.substring(0, fullName.length - direction.length).trim();
      return { building, direction };
    }
  }

  // If no direction is found, the whole name is the building name
  return { building: fullName };
}

/**
 * Loads building entrances from CSV and groups them by building
 */
export function loadBuildingEntrances(): GroupedEntrances {
  const entrances: BuildingEntrance[] = [];
  const grouped: GroupedEntrances = {};

  // Skip the header row and parse each CSV line
  const lines = entrancesData.split('\n').slice(1);
  
  for (const line of lines) {
    if (!line.trim()) continue; // Skip empty lines
    
    const [fullName, latStr, lonStr] = line.split(',');
    if (!fullName || !latStr || !lonStr) continue;
    
    const lat = parseFloat(latStr);
    const lon = parseFloat(lonStr);
    
    if (isNaN(lat) || isNaN(lon)) continue;
    
    const { building, direction } = parseEntranceName(fullName);
    
    const entrance: BuildingEntrance = {
      fullName,
      building,
      direction,
      lat,
      lon
    };
    
    entrances.push(entrance);
    
    // Group by building name
    if (!grouped[building]) {
      grouped[building] = [];
    }
    grouped[building].push(entrance);
  }
  
  return grouped;
}

// Export a buildings list for dropdown selection
export function getBuildingsList(groupedEntrances: GroupedEntrances): string[] {
  return Object.keys(groupedEntrances).sort();
}
