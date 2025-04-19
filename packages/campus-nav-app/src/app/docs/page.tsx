


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
                            <p>Documentation on how to build a custom GeoJSON Here</p>
                        </TabsContent>
                        <TabsContent value="api">
                            <p>API Documentatio Here</p>
                        </TabsContent>
                    </Tabs>
                </section>
            </main>
        </>
    );
}