import { SubPageHero } from "@/components/custom/SubPageHero";
import { Header } from "@/components/layout/Header"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function DocsPage() {
    return (
        <>
            <Header />
            <main className="flex-1 flex-row">
                <SubPageHero titleText="Docs" />
                <section className="mx-auto max-w-7xl px-4 py-12 pt-0 sm:px-6 lg:px-8">

                    <Tabs defaultValue="upload">
                        <TabsList>
                            <TabsTrigger value="upload">Uploading Custom Maps</TabsTrigger>
                            <TabsTrigger value="api">API Reference</TabsTrigger>
                        </TabsList>

                        <TabsContent value="upload">
                            <div className="space-y-6">
                                <h2 className="text-2xl font-bold">How to Create a Proper GeoJSON for GeoLoom</h2>

                                <p>
                                    To upload your own map into <strong>GeoLoom</strong>, there are a few important rules to follow.
                                    Please read carefully to ensure your map processes correctly.
                                </p>

                                <h3 className="text-xl font-semibold">Recommended Tool</h3>
                                <p>
                                    We recommend using{" "}
                                    <a
                                        href="https://geojson.io"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 underline"
                                    >
                                        geojson.io
                                    </a>{" "}
                                    for creating and editing your GeoJSON files. It’s simple and easy to use!
                                </p>

                                <h3 className="text-xl font-semibold">Drawing Your Map</h3>
                                <ul className="list-disc list-inside space-y-2">
                                    <li><strong>Polygons:</strong> Use the <strong>Polygon tool</strong> to draw each building, obstacle, or area you want to map.</li>
                                    <li><strong>Lines:</strong> Use the <strong>Line tool</strong> to draw hallways, walkways, or shortcuts you want users to traverse through.</li>
                                    <li><strong>Points (Entrances):</strong> Use the <strong>Point tool</strong> to mark each entrance.
                                        <br />
                                        <em>Important:</em> Points must be placed <strong>inside</strong> the corresponding polygon (building) they belong to.
                                    </li>
                                </ul>

                                <h3 className="text-xl font-semibold">Naming Requirements</h3>
                                <ul className="list-disc list-inside space-y-2">
                                    <li>Every <strong>polygon</strong> must have a property called <code>name</code> set to the <strong>building's name</strong>.</li>
                                    <li>Points (entrances) will be automatically processed and <strong>numbered clockwise</strong> like an analog clock:
                                        <ul className="list-disc list-inside ml-6">
                                            <li>Lower numbers (e.g., 1, 2) will be near the <strong>top-right</strong> of the building.</li>
                                            <li>Higher numbers (e.g., 10, 11) will be near the <strong>top-left</strong>.</li>
                                        </ul>
                                    </li>
                                </ul>

                                <h3 className="text-xl font-semibold">Setting Bounds</h3>
                                <p>
                                    Once you are finished placing all your polygons, lines, and points:
                                    <br />
                                    Use the <strong>Square (Rectangle) tool</strong> to draw a box around your entire map.
                                    <br />
                                    <em>This defines the bounds of your navigable area.</em>
                                </p>

                                <h3 className="text-xl font-semibold">Helpful Tip</h3>
                                <p>
                                    Refer to the <strong>provided example image</strong> as a guide while creating your map!
                                </p>
                                {/* Example Image Here */}
                                <img
                                    src="/images/example-map.png"
                                    alt="Example Map Layout"
                                    className="mx-auto my-8 rounded-lg shadow-lg"
                                />
                            </div>
                        </TabsContent>

                        <TabsContent value="api">
                            <p>API Documentation Here</p>
                        </TabsContent>
                    </Tabs>
                </section>
            </main>
        </>
    );
}
