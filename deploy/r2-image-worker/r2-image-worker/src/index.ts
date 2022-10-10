/**
 * Welcome to Cloudflare Workers! This is your first worker.
 *
 * - Run `wrangler dev src/index.ts` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your worker in action
 * - Run `wrangler publish src/index.ts --name my-worker` to publish your worker
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */

/* R2 Image Worker for parsnip.
   Worker name: r2-image-worker
   URL: https://r2-image-worker.upzone.workers.dev
   Connected to R2 Bucket name parsnip-images , where we store analysis images

   Publish with `wrangler publish`
   (wrangler is installed via npm i -g wrangler)

   See https://developers.cloudflare.com/r2/get-started for more info.
 */

export interface Env {
  // Example binding to KV. Learn more at https://developers.cloudflare.com/workers/runtime-apis/kv/
  // MY_KV_NAMESPACE: KVNamespace;
  //
  // Example binding to Durable Object. Learn more at https://developers.cloudflare.com/workers/runtime-apis/durable-objects/
  // MY_DURABLE_OBJECT: DurableObjectNamespace;
  //
  // Bindings to R2. Learn more at https://developers.cloudflare.com/workers/runtime-apis/r2/
  // Configured via cloudflare dashboard:
  parsnip_images: R2Bucket;
}

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {

    const url = new URL(request.url);
    const key = url.pathname.slice(1);

    switch (request.method) {
      // case 'PUT':
      //   await env.parsnip_images.put(key, request.body);
      //   return new Response(`Put ${key} successfully!`);
      case
      'GET'
      :
        const object = await env.parsnip_images.get(key);

        if (object === null) {
          return new Response('Object Not Found', { status: 404 });
        }

        const headers = new Headers();
        object.writeHttpMetadata(headers);
        headers.set('etag', object.httpEtag);

        return new Response(object.body, {
          headers,
        });
      // case 'DELETE':
      //   await env.MY_BUCKET.delete(key);
      //   return new Response('Deleted!');

      default:
        return new Response('Method Not Allowed', {
          status: 405,
          headers: {
            Allow: 'PUT, GET, DELETE',
          },
        });
    }
  },
};
