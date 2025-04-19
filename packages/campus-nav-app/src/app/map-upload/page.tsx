"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { SubPageHero } from "@/components/custom/SubPageHero"
import { Header } from "@/components/layout/Header"
import { FileUpload } from "@/components/ui/file-upload"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import Link from "next/link";
import { validateGeoJSON } from "@/lib/geojson-validator";

export default function MapUploadPage() {
    const router = useRouter()
    const [selectedFile, setSelectedFile] = React.useState<File | null>(null)
    const [mapName, setMapName] = React.useState("")
    const [errors, setErrors] = React.useState<string[]>([])
    const [isSubmitting, setIsSubmitting] = React.useState(false)

    const handleFileChange = async (files: File[]) => {
        const file = files[0]
        if (!file) return;

        setSelectedFile(file)
        setErrors([])
        try {
            const text = await file.text()
            const json = JSON.parse(text)
            // Pass file size to validation
            const validationErrors = validateGeoJSON(json, file.size)
            setErrors(validationErrors)
        } catch (e) {
            if (e instanceof SyntaxError) {
                setErrors(["Invalid JSON file: Check syntax."]);
            } else {
                setErrors(["Error reading or parsing file."]);
                console.error("File processing error:", e);
            }
        }
    }

    const handleSubmit = async () => {
        if (!selectedFile || errors.length > 0 || !mapName) return
        setIsSubmitting(true)
        // TODO: implement actual upload API call
        router.push("/map-upload/success")
    }

    return (
        <>
            <Header />
            <main className="flex-1">
                <SubPageHero titleText="Upload Custom Map" />

                <div className="px-4 lg:px-8 space-y-6">
                    <FileUpload onChange={handleFileChange} />
                </div>
                <section className="mx-auto max-w-2xl px-4 py-12 sm:px-6 lg:px-8 space-y-6">
                    {selectedFile && (
                        <div className="space-y-4">
                            {errors.length > 0 ? (
                                <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded space-y-2">
                                    <p className="font-semibold">We encountered some issues with your GeoJSON:</p>
                                    <ul className="mt-1 list-disc list-inside ml-4">
                                        {Array.from(new Set(errors)).slice(0, 3).map((e, i) => (
                                            <li key={i}>{e}</li>
                                        ))}
                                    </ul>
                                    {errors.length > 3 && (
                                        <p className="text-sm">…and {errors.length - 3} more issues.</p>
                                    )}
                                    <p className="text-sm">
                                        Please update your file to meet requirements. See our{' '}
                                        <Link href="/docs#uploading-custom-maps" className="underline">
                                            GeoJSON upload guide
                                        </Link>{' '}
                                        for detailed specifications.
                                    </p>
                                </div>
                            ) : (
                                <div className="bg-green-50 border border-green-200 text-green-800 p-4 rounded">
                                    File is valid GeoJSON. You can now name and submit your map.
                                </div>
                            )}
                            <div className="space-y-1">
                                <Label htmlFor="mapName">Map Name</Label>
                                <Input
                                    id="mapName"
                                    placeholder="Enter map name"
                                    value={mapName}
                                    onChange={(e) => setMapName(e.target.value)}
                                />
                            </div>
                            <Button
                                variant="default"
                                size="default"
                                onClick={handleSubmit}
                                disabled={isSubmitting || errors.length > 0 || !mapName}
                            >
                                {isSubmitting ? "Submitting..." : "Submit"}
                            </Button>
                        </div>
                    )}
                </section>
            </main>
        </>
    )
}