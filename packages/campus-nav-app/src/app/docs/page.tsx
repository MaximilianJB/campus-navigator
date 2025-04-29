import { SubPageHero } from "@/components/custom/SubPageHero";
import { Header } from "@/components/layout/Header"
import CodeBlock from "@/components/ui/CodeBlock";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Image from "next/image";

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
                                    <li>Every <strong>polygon</strong> must have a property called <code>name</code> set to the <strong>building&apos;s name</strong>.</li>
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
                                <Image
                                    src="/images/example_geojson.png"
                                    alt="Example Map Layout"
                                    width={800}
                                    height={600}
                                    className="my-8 rounded-lg shadow-lg"
                                />
                            </div>
                        </TabsContent>
                        <TabsContent value="api">
                            <div className="space-y-6">
                                <h2 className="text-2xl font-bold">Pathfinding API</h2>
                                <p>This directory contains the API for calculating the shortest path between two geographical coordinates using the <strong>A*</strong> pathfinding algorithm. The API is hosted on <strong>Google Cloud Run</strong> and exposes a single endpoint for path calculations.</p>

                                <h3 className="text-xl font-semibold">Files Overview</h3>
                                <h4 className="text-lg font-semibold"><code>main.py</code></h4>
                                <ul className="list-disc list-inside space-y-1">
                                    <li>Implements the API using a web framework (e.g., FastAPI or Flask).</li>
                                    <li>Accepts <strong>POST</strong> requests with JSON payloads.</li>
                                    <li>Processes start and end latitude/longitude coordinates.</li>
                                    <li>Returns the <strong>shortest path</strong> as a list of coordinates.</li>
                                </ul>
                                <h4 className="text-lg font-semibold"><code>Dockerfile</code></h4>
                                <ul className="list-disc list-inside space-y-1">
                                    <li>Defines the containerization setup for deploying the API.</li>
                                    <li>Specifies dependencies and the execution environment for Google Cloud Run.</li>
                                </ul>

                                <h3 className="text-xl font-semibold">API Usage</h3>
                                <h4 className="text-lg font-semibold">Endpoint</h4>
                                <p><code>POST https://calculatecampuspath-842151361761.us-central1.run.app</code></p>

                                <h4 className="text-lg font-semibold">Request Format</h4>
                                <p>The API accepts a <strong>JSON payload</strong> with the following fields:</p>
                                <ul className="list-disc list-inside space-y-1">
                                    <li><code>start_lat</code> (float): Latitude of the starting point.</li>
                                    <li><code>start_lng</code> (float): Longitude of the starting point.</li>
                                    <li><code>end_lat</code> (float): Latitude of the destination point.</li>
                                    <li><code>end_lng</code> (float): Longitude of the destination point.</li>
                                </ul>

                                <h4 className="text-lg font-semibold">Example Request (cURL)</h4>
                                <CodeBlock code={`curl -X POST -H "Content-Type: application/json" -d '{"start_lat": 47.6625, "start_lng": -117.4090, "end_lat": 47.6700, "end_lng": -117.3970}' https://calculatecampuspath-842151361761.us-central1.run.app`} />

                                <h4 className="text-lg font-semibold">Response Format</h4>
                                <p>The response contains a <strong>list of latitude/longitude coordinates</strong> representing the shortest path.</p>
                                <CodeBlock code={`{
  "path": [
    [47.66249194241168, -117.40901253340753],
    [47.66249194241168, -117.40898582469885],
    [47.66249194241168, -117.40895911599014]
  ]
}`} />

                                <h3 className="text-xl font-semibold">Deployment</h3>
                                <ul className="list-disc list-inside space-y-1">
                                    <li>The API is containerized using <strong>Docker</strong>.</li>
                                    <li>Hosted on <strong>Google Cloud Run</strong> for scalability and serverless execution.</li>
                                </ul>

                                <h3 className="text-xl font-semibold">Running Locally</h3>
                                <ol className="list-decimal list-inside space-y-1">
                                    <li>Navigate to the <code>/api</code> directory.</li>
                                    <li>Build the Docker image: <code>docker build -t calculatecampuspath:test .</code></li>
                                    <li>Run the container: <code>docker run -p 8080:8080 -e PORT=8080 calculatecampuspath:test</code></li>
                                    <li>
                                        Send request to local server:
                                        <CodeBlock code={`curl -X POST -H "Content-Type: application/json" -d '{"start_lat": 47.6625, "start_lng": -117.4090, "end_lat": 47.6700, "end_lng": -117.3970}' http://localhost:8080`} />
                                    </li>
                                </ol>
                            </div>
                        </TabsContent>
                    </Tabs>
                </section >
            </main >
        </>
    );
}