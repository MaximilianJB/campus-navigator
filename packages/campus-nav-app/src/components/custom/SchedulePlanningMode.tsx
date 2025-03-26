'use client';

import { useEffect, useState } from 'react';
import { Building } from '@/lib/buildingEntrances';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { GripVertical, Trash2, MapPin, Clock } from 'lucide-react';
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

// Define interfaces for our data structures
interface ClassItem {
    id: string;
    name: string;
    buildingName: string;
    entranceName: string;
    lat: number;
    lon: number;
}

export interface ScheduleEntrance {
    lat: number;
    lon: number;
    name: string;
}

interface SchedulePlanningModeProps {
    onEntrancesChange: (entrances: ScheduleEntrance[]) => void;
    onPathGenerated?: (path: [number, number][]) => void;
}

// The sortable class item component
function SortableClassItem({
    item,
    index,
    onRemove
}: {
    item: ClassItem;
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
            className="bg-card border rounded-lg mb-2 overflow-hidden"
        >
            <div className="p-3 flex items-center gap-2">
                <div
                    className="cursor-grab touch-manipulation"
                    {...attributes}
                    {...listeners}
                >
                    <GripVertical className="h-5 w-5 text-muted-foreground" />
                </div>
                <div className="flex-grow flex flex-col">
                    <div className="flex items-center gap-2">
                        <div className="flex items-center justify-center bg-primary text-primary-foreground rounded-full w-6 h-6 text-xs font-medium">
                            {index + 1}
                        </div>
                        <div className="font-medium">{item.name}</div>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        <span>{item.buildingName} - {item.entranceName}</span>
                    </div>
                </div>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onRemove(item.id)}
                    className="h-8 w-8"
                >
                    <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
            </div>
        </div>
    );
}

export default function SchedulePlanningMode({
    onEntrancesChange,
    onPathGenerated
}: SchedulePlanningModeProps) {
    const [buildings, setBuildings] = useState<Building[]>([]);
    const [selectedBuilding, setSelectedBuilding] = useState<string>('');
    const [selectedEntrance, setSelectedEntrance] = useState<string>('');
    const [className, setClassName] = useState('');
    const [classes, setClasses] = useState<ClassItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isGeneratingPath, setIsGeneratingPath] = useState(false);
    const [pathError, setPathError] = useState<string | null>(null);

    // Create sensors for drag-and-drop
    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    // Get the current building based on selection
    const currentBuilding = buildings.find(b => b.name === selectedBuilding);

    // Update parent component when classes change
    useEffect(() => {
        // Generate entrances data to pass to map component
        const updatedEntrances = classes.map((classItem, index) => ({
            lat: classItem.lat,
            lon: classItem.lon,
            name: `${index + 1}: ${classItem.name} - ${classItem.buildingName}`
        }));

        onEntrancesChange(updatedEntrances);
    }, [classes, onEntrancesChange]);

    // Load building entrances data
    useEffect(() => {
        async function loadBuildingEntrances() {
            try {
                setIsLoading(true);
                const response = await fetch('/building_entrances.json');
                if (!response.ok) {
                    throw new Error('Failed to load building entrances data');
                }
                const data = await response.json();
                setBuildings(data);
                // Set default selections if available
                if (data.length > 0) {
                    setSelectedBuilding(data[0].name);
                    if (data[0].entrances.length > 0) {
                        setSelectedEntrance(data[0].entrances[0].name);
                    }
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
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
    const getSelectedEntranceCoords = () => {
        if (!selectedBuilding || !selectedEntrance) return null;

        const building = buildings.find(b => b.name === selectedBuilding);
        if (!building) return null;

        const entrance = building.entrances.find(e => e.name === selectedEntrance);
        if (!entrance) return null;

        return { lat: entrance.lat, lon: entrance.lon };
    };

    // Handle adding a class to the schedule
    const handleAddClass = () => {
        if (!className.trim() || !selectedBuilding || !selectedEntrance) {
            return;
        }

        const coords = getSelectedEntranceCoords();
        if (!coords) return;

        const newClass: ClassItem = {
            id: Date.now().toString(),
            name: className.trim(),
            buildingName: selectedBuilding,
            entranceName: selectedEntrance,
            lat: coords.lat,
            lon: coords.lon
        };

        setClasses(prev => [...prev, newClass]);
        setClassName(''); // Reset class name input
    };

    // Handle removing a class from the schedule
    const handleRemoveClass = (id: string) => {
        setClasses(prev => prev.filter(c => c.id !== id));
    };

    // Handle drag end event for reordering
    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            setClasses((items) => {
                const oldIndex = items.findIndex(i => i.id === active.id);
                const newIndex = items.findIndex(i => i.id === over.id);

                return arrayMove(items, oldIndex, newIndex);
            });
        }
    };

    // Handle generate schedule
    const handleGenerateSchedule = async () => {
        if (classes.length < 2) {
            setPathError('You need at least two classes to generate a path');
            return;
        }

        setIsGeneratingPath(true);
        setPathError(null);

        try {
            // Convert classes to LocationPoint array for path generation
            const points: LocationPoint[] = classes.map(cls => ({
                lat: cls.lat,
                lon: cls.lon,
                name: cls.name
            }));

            console.log('Generating path for classes:', points);

            // Generate a path through all class locations
            const path = await generatePath(points);

            // Pass the generated path to the parent component if callback exists
            if (onPathGenerated) {
                onPathGenerated(path);
            }
        } catch (error) {
            if (error instanceof Error) {
                setPathError(`Failed to generate path: ${error.message}`);
            } else {
                setPathError('An unknown error occurred while generating the path');
            }
            console.error('Path generation error:', error);
        } finally {
            setIsGeneratingPath(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-4 h-64">
                <div className="text-lg">Loading building data...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center p-4 h-64">
                <div className="text-lg text-red-500">Error: {error}</div>
                <div className="mt-2">Please try reloading the page.</div>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6 w-full">
            {/* Form for adding a new class */}
            <Card>
                <CardHeader>
                    <CardTitle>Add Class to Schedule</CardTitle>
                    <CardDescription>
                        Enter class details and location
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-col gap-4">
                        <div className="grid grid-cols-1 gap-4">
                            <div className="space-y-2">
                                <label htmlFor="class-name" className="text-sm font-medium">
                                    Class Name
                                </label>
                                <Input
                                    id="class-name"
                                    value={className}
                                    onChange={(e) => setClassName(e.target.value)}
                                    placeholder="e.g. Introduction to Computer Science"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Building selection */}
                            <div className="space-y-2">
                                <label htmlFor="building-select" className="text-sm font-medium">
                                    Building
                                </label>
                                <Select
                                    value={selectedBuilding}
                                    onValueChange={handleBuildingChange}
                                >
                                    <SelectTrigger id="building-select">
                                        <SelectValue placeholder="Select a building" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {buildings.map((building) => (
                                            <SelectItem
                                                key={building.name}
                                                value={building.name}
                                            >
                                                {building.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Entrance selection */}
                            <div className="space-y-2">
                                <label htmlFor="entrance-select" className="text-sm font-medium">
                                    Entrance
                                </label>
                                <Select
                                    value={selectedEntrance}
                                    onValueChange={setSelectedEntrance}
                                    disabled={!currentBuilding || currentBuilding.entrances.length === 0}
                                >
                                    <SelectTrigger id="entrance-select">
                                        <SelectValue placeholder="Select an entrance" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {currentBuilding?.entrances.map((entrance) => (
                                            <SelectItem
                                                key={entrance.name}
                                                value={entrance.name}
                                            >
                                                {entrance.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>
                </CardContent>
                <CardFooter>
                    <Button onClick={handleAddClass} disabled={!className.trim() || !selectedBuilding || !selectedEntrance}>
                        Add to Schedule
                    </Button>
                </CardFooter>
            </Card>

            {/* Class schedule */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle>Your Class Schedule</CardTitle>
                        <CardDescription>
                            Drag and drop to reorder classes
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        <span>{classes.length} classes</span>
                    </div>
                </CardHeader>
                <CardContent>
                    {classes.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            No classes added yet. Add your first class above.
                        </div>
                    ) : (
                        <DndContext
                            sensors={sensors}
                            collisionDetection={closestCenter}
                            onDragEnd={handleDragEnd}
                        >
                            <SortableContext
                                items={classes.map(c => c.id)}
                                strategy={verticalListSortingStrategy}
                            >
                                {classes.map((classItem, index) => (
                                    <SortableClassItem
                                        key={classItem.id}
                                        item={classItem}
                                        index={index}
                                        onRemove={handleRemoveClass}
                                    />
                                ))}
                            </SortableContext>
                        </DndContext>
                    )}
                </CardContent>
            </Card>

            {/* Generate Schedule Card */}
            <Card>
                <CardHeader>
                    <CardTitle>Generate Schedule</CardTitle>
                    <CardDescription>
                        Generate a schedule for your classes
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Button
                        onClick={handleGenerateSchedule}
                        disabled={classes.length < 2 || isGeneratingPath}
                    >
                        {isGeneratingPath ? 'Generating...' : 'Generate Schedule'}
                    </Button>
                    {pathError && (
                        <p className="text-red-500 text-sm mt-2">{pathError}</p>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};
