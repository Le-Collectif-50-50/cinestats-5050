import type { MetadataRoute } from "next";

// Only deploy.yml (production) sets this build-arg to "true" — preview and
// local builds never do, so they disallow everything by default. Same
// pattern as NEXT_PUBLIC_UMAMI_WEBSITE_ID: no separate config to remember
// to flip when spinning up a new non-production environment.
const isIndexable = process.env.NEXT_PUBLIC_ALLOW_ROBOTS_INDEXING === "true";

export default function robots(): MetadataRoute.Robots {
  if (!isIndexable) {
    return {
      rules: {
        userAgent: "*",
        disallow: "/",
      },
    };
  }

  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
  };
}
