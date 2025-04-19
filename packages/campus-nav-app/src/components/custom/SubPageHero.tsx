export function SubPageHero({ titleText }: { titleText: string }) {
    return (
        <>
            <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="relative mb-4 overflow-hidden rounded-xl bg-gradient-to-br from-teal-50 via-white to-cyan-50 p-10 text-left shadow-sm">
                    {/* Grid overlay for map feel */}
                    <div
                        className="absolute inset-0 z-0 opacity-20"
                        style={{
                            backgroundImage:
                                'repeating-linear-gradient(90deg, #14b8a6 0px, #14b8a6 1px, transparent 1px, transparent 20px), ' +
                                'repeating-linear-gradient(0deg, #14b8a6 0px, #14b8a6 1px, transparent 1px, transparent 20px)',
                        }}
                    />

                    {/* Text content */}
                    <div className="relative flex flex-col gap-4 z-40">
                        <h2 className="text-3xl font-bold tracking-tight text-gray-900">
                            {titleText}
                        </h2>
                    </div>
                </div>
            </section>
        </>
    );
}