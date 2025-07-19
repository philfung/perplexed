# Cloudflare Deployment Strategy

This Cloudflare starter deployment separates frontend and backend concerns, leveraging Cloudflare's edge infrastructure for static asset serving while maintaining total flexibility to run any Python app on the backend.

## Architecture Overview

1. **Frontend Bundling**: The React frontend is built locally using `bun run build:cloudflare-{local,prod}` and outputs to `./dist/frontend-{dev,prod}`

2. **Frontend Serving**: Cloudflare Worker Assets serve the static frontend files directly from the edge via the `[assets]` configuration in `wrangler.toml`

3. **Backend Container**: The FastAPI application runs in a Cloudflare Container on port 30001, handling only API requests (`/stream` and `/env` endpoints)

4. **Request Routing**: The Worker script (`index.ts`) routes API requests to the container instance while serving static assets for all other paths

## Key Differences from Traditional Dockerfile Deployment

### Cloudflare Approach

- **Separation of Concerns**: Frontend assets served by Cloudflare edge, backend runs in container
- **No Nginx Required**: Cloudflare Workers handle static asset serving and API routing
- **Edge Performance**: Frontend assets cached and served from Cloudflare's global network
- **Container Simplicity**: `Dockerfile-cloudflare` only contains Python/FastAPI dependencies
- **Dynamic Scaling**: Container instances can scale based on demand with `max_instances` configuration

### Alternative Monolith Approach (see repo root `./Dockerfile`)

- **Single Container**: Both frontend and backend run in the same container
- **Nginx Proxy**: Nginx serves static files and reverse proxies API requests to FastAPI
- **Self-Contained**: All components packaged together in one deployable unit
- **Port Management**: Nginx listens on port 80, proxies to FastAPI on localhost:30001

## Benefits of Cloudflare Deployment

- **Better Performance**: Static assets served from edge locations closest to users
- **Cost Efficiency**: Backend containers only run when handling API requests
- **Simplified Backend**: No need for Nginx configuration or static file handling in container
- **Auto-Scaling**: Cloudflare handles frontend scaling automatically, backend scales via container settings

## Notes

- This strategy does not use [Cloudflare Python Workers](https://developers.cloudflare.com/workers/languages/python/). Python Workers (no container) [limits the libraries](https://developers.cloudflare.com/workers/languages/python/stdlib/) you can use, and thus far this repo (and most Python apps) have not been adapted to fit in the Cloudflare Python Worker runtime limitations.
