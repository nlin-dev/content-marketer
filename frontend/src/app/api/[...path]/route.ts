const BACKEND = process.env.BACKEND_URL || 'http://localhost:8000';

async function proxy(request: Request) {
  const url = new URL(request.url);
  const target = `${BACKEND}${url.pathname}${url.search}`;

  const headers = new Headers(request.headers);
  headers.delete('host');

  const init: RequestInit = {
    method: request.method,
    headers,
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = request.body;
    // @ts-expect-error duplex required for streaming body
    init.duplex = 'half';
  }

  const res = await fetch(target, init);

  const responseHeaders = new Headers(res.headers);
  responseHeaders.delete('transfer-encoding');

  return new Response(res.body, {
    status: res.status,
    statusText: res.statusText,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
