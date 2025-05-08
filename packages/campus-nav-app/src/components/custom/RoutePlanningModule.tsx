// src/components/custom/RoutePlanningMode.tsx
'use client';

import { useEffect, useState, useCallback } from 'react';
import { Building } from '@/lib/buildingEntrances';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { GripVertical, Trash2, MapPin, Eye, Navigation, Loader2, MapPinned } from 'lucide-react';
import {
    DndContext,
    DragEndEvent,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors
} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { generatePath, LocationPoint } from '@/lib/pathUtils';
import Link from 'next/link';

// Define interfaces for our data structures
interface PinItem {
    id: string;
    name: string;
    buildingName: string;
    entranceName: string;
    lat: number;
    lon: number;
}

export interface RouteEntrance {
    lat: number;
    lon: number;
    name: string;
}

interface RoutePlanningModeProps {
    onEntrancesChange: (entrances: RouteEntrance[]) => void;
    onPathGenerated?: (path: [number, number][]) => void;
    setCameraMode: (mode: 'aerial' | 'start' | 'flyBy') => void;
    cameraMode: 'aerial' | 'start' | 'flyBy';
}

// The sortable pin item component
function SortablePinItem({
    item,
    index,
    onRemove
}: {
    item: PinItem;
    index: number;
    onRemove: (id: string) => void
}) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition
    } = useSortable({ id: item.id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className="bg-card border rounded-lg mb-2 overflow-hidden shadow-sm"
        >
            <div className="p-3 flex items-center gap-2">
                <div
                    className="cursor-grab touch-manipulation p-1"
                    {...attributes}
                    {...listeners}
                >
                    <GripVertical className="h-5 w-5 text-muted-foreground" />
                </div>
                <div className="flex-grow flex flex-col">
                    <div className="flex items-center gap-2">
                        <div className="flex items-center justify-center bg-teal-500 text-white rounded-full w-6 h-6 text-xs font-semibold">
                            {index + 1}
                        </div>
                        <div className="font-medium">{item.name}</div>
                    </div>
                    <div className="flex items-center gap-1.5 mt-1 text-sm text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        <span>{item.buildingName} - {item.entranceName}</span>
                    </div>
                </div>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onRemove(item.id)}
                    className="h-8 w-8 text-destructive hover:bg-destructive/10"
                >
                    <Trash2 className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}

export default function RoutePlanningMode({
    onEntrancesChange,
    onPathGenerated,
    setCameraMode, // Destructure props
    cameraMode
}: RoutePlanningModeProps) {
    const [buildings, setBuildings] = useState<Building[]>([]);
    const [selectedBuilding, setSelectedBuilding] = useState<string>('');
    const [selectedEntrance, setSelectedEntrance] = useState<string>('');
    const [pinName, setPinName] = useState('');
    const [pins, setPins] = useState<PinItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isGeneratingPath, setIsGeneratingPath] = useState(false);
    const [pathError, setPathError] = useState<string | null>(null);
    const [apiError, setApiError] = useState<string | null>(null);


    // Create sensors for drag-and-drop
    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    // Get the current building based on selection
    const currentBuilding = buildings.find(b => b.name === selectedBuilding);

    // Update parent component when pins change
    useEffect(() => {
        // Generate entrances data to pass to map component
        const updatedEntrances = pins.map((pinItem, index) => ({
            lat: pinItem.lat,
            lon: pinItem.lon,
            name: `${index + 1}: ${pinItem.name}` // Simplified name for pin
        }));
        onEntrancesChange(updatedEntrances);
    }, [pins, onEntrancesChange]);

    // Load building entrances data
    useEffect(() => {
        async function loadBuildingEntrances() {
            try {
                setIsLoading(true);
                setError(null); // Reset error before fetch
                const response = await fetch('/building_entrances.json');
                if (!response.ok) {
                    throw new Error(`Failed to load building entrances data (Status: ${response.status})`);
                }
                const data = await response.json();
                if (!Array.isArray(data) || data.length === 0) {
                    throw new Error('Building entrances data is empty or invalid');
                }
                setBuildings(data);
                // Set default selections if available
                if (data.length > 0) {
                    setSelectedBuilding(data[0].name);
                    if (data[0].entrances.length > 0) {
                        setSelectedEntrance(data[0].entrances[0].name);
                    } else {
                        setSelectedEntrance(''); // Handle case with building but no entrances
                    }
                } else {
                    setSelectedBuilding('');
                    setSelectedEntrance('');
                }
            } catch (err) {
                const message = err instanceof Error ? err.message : 'An unknown error occurred';
                setError(`Error loading locations: ${message}. Please ensure 'building_entrances.json' is present and correct in the public folder.`);
                console.error('Error loading building entrances:', err);
            } finally {
                setIsLoading(false);
            }
        }

        loadBuildingEntrances();
    }, []);


    // Handle building selection change
    const handleBuildingChange = (value: string) => {
        setSelectedBuilding(value);
        // Reset entrance selection
        const building = buildings.find(b => b.name === value);
        if (building && building.entrances.length > 0) {
            setSelectedEntrance(building.entrances[0].name);
        } else {
            setSelectedEntrance('');
        }
    };

    // Get selected entrance coordinates
    const getSelectedEntranceCoords = useCallback(() => {
        if (!selectedBuilding || !selectedEntrance) return null;
        const building = buildings.find(b => b.name === selectedBuilding);
        if (!building) return null;
        const entrance = building.entrances.find(e => e.name === selectedEntrance);
        if (!entrance) return null;
        return { lat: entrance.lat, lon: entrance.lon };
    }, [selectedBuilding, selectedEntrance, buildings]);


    // Handle adding a new pin
    const handleAddPin = () => {
        const coords = getSelectedEntranceCoords();
        if (!pinName.trim() || !coords) {
            // Add some user feedback here if desired (e.g., toast notification)
            console.warn("Pin name or coordinates missing");
            return;
        }

        const newPin: PinItem = {
            id: Date.now().toString(), // Simple unique ID
            name: pinName.trim(),
            buildingName: selectedBuilding,
            entranceName: selectedEntrance,
            lat: coords.lat,
            lon: coords.lon,
        };

        setPins(currentPins => [...currentPins, newPin]);
        setPinName(''); // Clear input field
    };

    // Handle removing a pin
    const handleRemovePin = (id: string) => {
        setPins(currentPins => currentPins.filter(pin => pin.id !== id));
    };

    // Handle drag-and-drop end event
    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            setPins((items) => {
                const oldIndex = items.findIndex(item => item.id === active.id);
                const newIndex = items.findIndex(item => item.id === over.id);
                return arrayMove(items, oldIndex, newIndex);
            });
        }
    };

    // Handle generating the path
    const handleGeneratePath = async () => {
        if (pins.length < 2) {
            setPathError("Please add at least two pins to generate a route.");
            return;
        }
        setPathError(null);
        setApiError(null); // Reset API error
        setIsGeneratingPath(true);

        const waypoints: LocationPoint[] = pins.map(pin => ({
            lat: pin.lat,
            lon: pin.lon
        }));

        try {
            const path = await generatePath(waypoints);
            if (onPathGenerated) {
                onPathGenerated(path);
            }
            setCameraMode('aerial'); // Switch to aerial view on successful path generation
        } catch (error) {
            console.error('Failed to generate path:', error);
            const message = error instanceof Error ? error.message : 'An unknown error occurred during path generation.';
            setApiError(`Route generation failed: ${message}`);
        } finally {
            setIsGeneratingPath(false);
        }
    };

    if (isLoading) {
        return <div className="flex justify-center items-center h-full"><Loader2 className="h-8 w-8 animate-spin text-teal-500" /></div>;
    }

    if (error) {
        return <div className="text-destructive p-4 bg-destructive/10 rounded-md">{error}</div>;
    }

    return (
        <Card className="h-full flex flex-col border-0 shadow-none rounded-none">
            <CardHeader className="pb-4">
                <CardTitle className="text-xl font-semibold flex flex-row justify-between pb-4">

                    <Link
                        href="/"
                        className="group flex items-center text-2xl font-bold tracking-tight"
                    >
                        <div className="flex items-center gap-2 transition-colors group-hover:text-teal-500">
                            <MapPinned className="h-6 w-6 text-teal-500" />
                            <span className="font-bold text-foreground tracking-tight">
                                <span className="text-teal-500">Geo</span>Loom
                            </span>
                        </div>
                    </Link>

                    <Link href={'/'}>
                        <Button variant={'ghost'}>Go back to home</Button>
                    </Link>
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                    Add pins by selecting a building and entrance, then arrange them to create your route.
                </p>
            </CardHeader>
            <CardContent className="flex-grow overflow-y-auto pr-3 space-y-4">
                {/* Pin Adding Section */}
                <div className="space-y-3 p-4 border rounded-lg bg-background">
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Add New Pin</h3>
                    <Input
                        placeholder="Pin Name (e.g., 'Start', 'Library')"
                        value={pinName}
                        onChange={(e) => setPinName(e.target.value)}
                    />
                    <Select value={selectedBuilding} onValueChange={handleBuildingChange}>
                        <SelectTrigger>
                            <SelectValue placeholder="Select Building" />
                        </SelectTrigger>
                        <SelectContent>
                            {buildings.map(building => (
                                <SelectItem key={building.name} value={building.name}>
                                    {building.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <Select
                        value={selectedEntrance}
                        onValueChange={setSelectedEntrance}
                        disabled={!currentBuilding || currentBuilding.entrances.length === 0}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select Entrance" />
                        </SelectTrigger>
                        <SelectContent>
                            {currentBuilding?.entrances.map(entrance => (
                                <SelectItem key={entrance.name} value={entrance.name}>
                                    {entrance.name} ({entrance.lat.toFixed(4)}, {entrance.lon.toFixed(4)})
                                </SelectItem>
                            ))}
                            {currentBuilding && currentBuilding.entrances.length === 0 && (
                                <div className="px-2 py-1.5 text-sm text-muted-foreground">No entrances available</div>
                            )}
                        </SelectContent>
                    </Select>
                    <Button onClick={handleAddPin} className="w-full bg-teal-500 hover:bg-teal-600 text-white" disabled={!pinName.trim() || !selectedBuilding || !selectedEntrance}>
                        Add Pin
                    </Button>
                </div>

                {/* Pin List Section */}
                {pins.length > 0 && (
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium text-muted-foreground mb-2">Route Pins</h3>
                        <DndContext
                            sensors={sensors}
                            collisionDetection={closestCenter}
                            onDragEnd={handleDragEnd}
                        >
                            <SortableContext
                                items={pins}
                                strategy={verticalListSortingStrategy}
                            >
                                {pins.map((pin, index) => (
                                    <SortablePinItem
                                        key={pin.id}
                                        item={pin}
                                        index={index}
                                        onRemove={handleRemovePin}
                                    />
                                ))}
                            </SortableContext>
                        </DndContext>
                    </div>
                )}
                {pins.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-4">Your route is empty. Add some pins!</p>
                )}
            </CardContent>
            <div className="p-4 border-t space-y-3">
                {/* Camera Controls */}
                {pins.length > 0 && (
                    <div>
                        <h3 className="text-sm font-medium mb-2">Camera View</h3>
                        <div className="flex flex-wrap gap-2">
                            <Button
                                variant={cameraMode === 'aerial' ? 'default' : 'outline'}
                                onClick={() => setCameraMode('aerial')}
                                className={`flex-1 ${cameraMode === 'aerial' ? 'bg-teal-500 hover:bg-teal-600 text-white' : ''}`}
                                size="sm"
                            >
                                <Eye className="mr-2 h-3.5 w-3.5" /> Aerial View
                            </Button>
                            <Button
                                variant={cameraMode === 'start' ? 'default' : 'outline'}
                                onClick={() => setCameraMode('start')}
                                className={`flex-1 ${cameraMode === 'start' ? 'bg-teal-500 hover:bg-teal-600 text-white' : ''}`}
                                size="sm"
                            >
                                <Navigation className="mr-2 h-3.5 w-3.5" /> Start View
                            </Button>
                            <Button
                                variant={cameraMode === 'flyBy' ? 'default' : 'outline'}
                                onClick={() => setCameraMode('flyBy')}
                                className={`flex-1 ${cameraMode === 'flyBy' ? 'bg-teal-500 hover:bg-teal-600 text-white' : ''}`}
                                size="sm"
                            >
                                <Navigation className="mr-2 h-3.5 w-3.5 animate-pulse" /> Fly By Tour 🚀
                            </Button>
                        </div>
                        {cameraMode === 'flyBy' && (
                            <p className="text-xs text-muted-foreground mt-2">
                                Sit back and enjoy an immersive tour along your route!
                            </p>
                        )}
                    </div>
                )}

                {/* Generate Path Button */}
                <Button
                    onClick={handleGeneratePath}
                    className="w-full"
                    disabled={isGeneratingPath || pins.length < 2}
                >
                    {isGeneratingPath ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Generating Route...
                        </>
                    ) : (
                        'Generate Route'
                    )}
                </Button>


                {pathError && <p className="text-sm text-destructive text-center">{pathError}</p>}
                {apiError && <p className="text-sm text-destructive text-center">{apiError}</p>}
            </div>
        </Card>
    );
}

// Helper component required by dnd-kit for sortable items
// We need to ensure the SortablePinItem receives the id prop correctly
// const SortablePinItemWrapper = ({ id, item, index, onRemove }: { id: string; item: PinItem; index: number; onRemove: (id: string) => void }) => {
//     const sortable = useSortable({ id });
//     return <SortablePinItem item={item} index={index} onRemove={onRemove} {...sortable} />;
// };