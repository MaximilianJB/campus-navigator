"use client";

interface SchedulePlanningModeProps {
  path: [number, number][] | null;
  setPath: (path: [number, number][] | null) => void;
  cameraMode: 'aerial' | 'start';
  setCameraMode: (mode: 'aerial' | 'start') => void;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export default function SchedulePlanningMode({ path, setPath, cameraMode, setCameraMode }: SchedulePlanningModeProps) {
  return (
    <div className="flex flex-col flex-1 gap-6">
      <div className="p-6 bg-gray-100 rounded-lg">
        <h3 className="text-lg font-medium mb-4">Schedule Planning</h3>
        <p className="text-gray-600">This feature is coming soon. Stay tuned!</p>
      </div>
    </div>
  );
}
