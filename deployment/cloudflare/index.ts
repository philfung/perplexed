import { Container, getRandom } from "@cloudflare/containers";

const INSTANCE_COUNT = 2;

export class PerplexedContainer extends Container {
  defaultPort = 30000;
  sleepAfter = "15m";
}

export default {
  async fetch(
    request: Request,
    env: { PERPLEXED_CONTAINER: DurableObjectNamespace<PerplexedContainer> },
  ): Promise<Response> {
    const containerInstance = await getRandom(env.PERPLEXED_CONTAINER, INSTANCE_COUNT);
    return containerInstance.fetch(request);
  },
};
