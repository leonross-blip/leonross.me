import { defineCollection, z } from "astro:content";
import { glob, file } from "astro/loaders";
import { parse } from "yaml";

// Posts: Markdown files in src/content/posts/.
// Files starting with "_" (the templates) are excluded from the build.
// The schema validates only the keys the site uses; any extra frontmatter
// keys (e.g. Obsidian metadata) are silently ignored, never a build error.
const posts = defineCollection({
  loader: glob({ pattern: ["**/*.md", "!_*"], base: "./src/content/posts" }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    type: z.enum(["paper", "company"]),
    summary: z.string(),
    link: z.string().url().optional(),
    tags: z.array(z.string()).default([]),
  }),
});

// Projects: a single YAML list. Ids are derived from position, so entries
// in projects.yaml don't need an id field.
const projects = defineCollection({
  loader: file("./src/content/projects.yaml", {
    parser: (text) =>
      (parse(text) ?? []).map((p: Record<string, unknown>, i: number) => ({
        id: String(i),
        ...p,
      })),
  }),
  schema: z.object({
    title: z.string(),
    oneLiner: z.string(),
    github: z.string().url().optional(),
    status: z.string(),
  }),
});

export const collections = { posts, projects };
