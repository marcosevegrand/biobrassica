import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const products = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/products' }),
  schema: z.object({
    title: z.string(),
    category: z.string(),
    priceDisplay: z.string(),
    image: z.string(),
    isHighlight: z.boolean().default(false),
    locations: z.array(z.string()),
    lang: z.string().default('pt'),
  }),
});

const recipes = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/recipes' }),
  schema: z.object({
    title: z.string(),
    prepTime: z.string(),
    difficulty: z.string(),
    tags: z.array(z.string()),
    image: z.string(),
    ingredientsList: z.array(z.string()),
    featuredProducts: z.array(z.string()).default([]),
    lang: z.string().default('pt'),
  }),
});

const categories = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/categories' }),
  schema: z.object({
    key: z.string(),
    name: z.string(),
    image: z.string(),
    order: z.number().int().nonnegative().default(0),
    lang: z.string().default('pt'),
  }),
});

export const collections = { products, recipes, categories };
