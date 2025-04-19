import { NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { Storage, File } from '@google-cloud/storage';

// Check for credentials
if (
  !process.env.GCP_PROJECT_ID ||
  !process.env.GCP_CLIENT_EMAIL ||
  !process.env.GCP_PRIVATE_KEY
) {
  throw new Error('Missing Google Cloud credentials');
}

const storage = new Storage({
  projectId: process.env.GCP_PROJECT_ID,
  credentials: {
    client_email: process.env.GCP_CLIENT_EMAIL!,
    private_key: process.env.GCP_PRIVATE_KEY!.replace(/\n/g, '\n'),
  },
});

const bucketName = 'gu-campus-maps';

export async function GET() {
  try {
    const bucket = storage.bucket(bucketName);
    const [, , apiResponse] = await bucket.getFiles({
      delimiter: '/',
      autoPaginate: false,
    });
    const prefixes: string[] = (apiResponse as { prefixes?: string[] }).prefixes || [];

    const maps = await Promise.all(
      prefixes.map(async (prefix) => {
        const name = prefix.replace(/\/$/, '');
        const [files] = await bucket.getFiles({ prefix });
        let createdAt = new Date().toISOString();
        if (files.length) {
          const times = files
            .map((f: File) => f.metadata.timeCreated)
            .filter((t): t is string => Boolean(t))
            .map((t) => new Date(t).getTime());
          if (times.length) {
            createdAt = new Date(Math.min(...times)).toISOString();
          }
        }
        return { name, createdAt };
      })
    );

    return NextResponse.json({ maps });
  } catch (error) {
    console.error(error);
    return NextResponse.json(
      { error: 'Failed to fetch maps' },
      { status: 500 }
    );
  }
}
