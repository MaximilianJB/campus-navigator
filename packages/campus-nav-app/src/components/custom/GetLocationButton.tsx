import React, { useState } from 'react';
import { Button } from '@/components/ui/button';

interface GetLocationButtonProps {
    onLocationObtained: (lat: number, long: number) => void;
}

const GetLocationButton: React.FC<GetLocationButtonProps> = ({ onLocationObtained }) => {
    const [isLoading, setIsLoading] = useState(false);

    const handleGetLocation = () => {
        if (navigator.geolocation) {
            setIsLoading(true);
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    setIsLoading(false);
                    const lat = position.coords.latitude;
                    const long = position.coords.longitude;
                    onLocationObtained(lat, long);
                },
                (error) => {
                    setIsLoading(false);
                    console.error('Error getting location:', error);
                }
            );
        } else {
            console.error('Geolocation is not supported by this browser.');
        }
    };

    return (
        <Button onClick={handleGetLocation} disabled={isLoading}>
            Get current location
        </Button>
    );
};

export default GetLocationButton;