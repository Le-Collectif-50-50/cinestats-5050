import { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  if (process.env.ANNOTATION_ENABLED !== 'true') return new Response(null, { status: 404 });
  if (request.method !== 'GET' && request.headers.get('origin') !== `${request.nextUrl.protocol}//${request.headers.get('host')}`) {
    return Response.json({ detail: 'Origine refusée' }, { status: 403 });
  }
  const { path } = await context.params;
  const route = path.join('/');
  if (!/^(posters|import\/allocine\/\d+|posters\/[\w-]+(?:\/(image|review|export))?)$/.test(route)) {
    return new Response(null, { status: 404 });
  }
  try {
    const upstream = await fetch(`${process.env.ANNOTATION_API_URL || 'http://127.0.0.1:5010'}/${route}`, {
      method: request.method,
      headers: { 'Content-Type': 'application/json' },
      body: request.method === 'GET' ? undefined : await request.text(),
      cache: 'no-store',
      signal: AbortSignal.timeout(90000),
    });
    const headers = new Headers({ 'Cache-Control': 'no-store' });
    for (const key of ['Content-Type', 'Content-Disposition']) {
      const value = upstream.headers.get(key);
      if (value) headers.set(key, value);
    }
    return new Response(upstream.body, { status: upstream.status, headers });
  } catch {
    return Response.json({ detail: 'Service d’annotation indisponible' }, { status: 503 });
  }
}

export { proxy as GET, proxy as POST, proxy as PUT };
