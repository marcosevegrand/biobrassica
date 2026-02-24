# 📄 BIOBRASSICA 2026: MASTER TECHNICAL & DESIGN SPECIFICATION
**Target Framework:** Astro.js + Tailwind CSS + Alpine.js/React (for minimal interactivity).
**Project Type:** Multi-language (PT, EN, FR) Digital Catalog & Content Hub. (No E-commerce checkout).
**Infrastructure:** Dockerized for local development and production deployment.

---

## 1. ART DIRECTION & DESIGN SYSTEM (Tailwind Config)
The aesthetic is "Eco-Minimalism" (inspired by *Maria Granel*). It must feel breathable, grounded, and premium.

### **Color Palette**
*   **Background (Paper):** `#FBF9F6` (Use this instead of pure white for all pages to reduce glare and feel organic).
*   **Primary Text & Accents (Forest):** `#2C3F2D` (Deep, elegant green).
*   **Secondary Accents (Terracotta/Clay):** `#B85C38` (Used for hover states, badges, and attention elements).
*   **Borders & Muted Text (Stone):** `#D1D1CC` (For subtle dividers) and `#6B6B6B` (for secondary text).

### **Typography**
*   **Headings (Serif):** `Playfair Display` or `Lora`. (Weight: 400 & italic). Used for all H1, H2, and Product Titles.
*   **Body Text (Sans-Serif):** `Inter` or `Montserrat`. (Weight: 300 & 400). Extremely clean and readable.
*   **UI Elements (Buttons/Tags):** Sans-serif, all-caps, widely spaced (`tracking-widest`, `text-xs`).

### **UI Components & Feel**
*   **Borders/Corners:** Minimal rounding (`rounded-sm` or square). No heavy drop shadows; use delicate 1px borders (`border-stone`) to separate items.
*   **Photography:** Images should take up large amounts of space. Use `object-cover` and `aspect-square` or `aspect-[3/4]` for product and recipe cards.

---

## 2. FILE & FOLDER ORGANIZATION (Astro Architecture)
The Code Agent must structure the project using Astro's Content Collections for easy data management.

```text
/
├── src/
│   ├── components/         # Reusable UI parts
│   │   ├── Global/         # Navbar.astro, Footer.astro, WhatsAppBtn.astro
│   │   ├── Cards/          # ProductCard.astro, RecipeCard.astro
│   │   └── Sections/       # HeroVideo.astro, InstaFeed.astro
│   ├── content/            # The "Database" (Markdown/JSON)
│   │   ├── config.ts       # Schema definitions
│   │   ├── products/       # .md files for each product
│   │   └── recipes/        # .md files for each recipe
│   ├── i18n/               # Translation dictionaries (ui.ts)
│   ├── layouts/            # BaseLayout.astro
│   └── pages/              
│       ├── [lang]/         # Dynamic language routing (pt, en, fr)
│       │   ├── index.astro            # Home
│       │   ├── quem-somos.astro       # About
│       │   ├── agricultura-bio.astro  # Agriculture
│       │   ├── loja/                  # Catalog 
│       │   │   └── index.astro
│       │   ├── receitas/              # Recipes
│       │   │   ├── index.astro
│       │   │   └── [slug].astro       # Single Recipe Page
│       │   └── contactos.astro        # Locations/Contact
└── tailwind.config.mjs
```

---

## 3. DATA STRUCTURE (Content Schemas)
Tell the agent to define these exact schemas in `src/content/config.ts`. You will add content by simply dropping `.md` files into the respective folders.

### **A. Product Schema (`content/products/`)**
```typescript
{
  id: string;             // e.g., "abobora-hokkaido"
  title: string;          // Product name
  category: string;       // "Fresco", "Mercearia", "Cosmética"
  priceDisplay: string;   // e.g., "2,50€ / kg" (String, since no calculation is needed)
  image: string;          // Path to image
  isHighlight: boolean;   // If true, shows on Homepage
  locations: string[];    // ["Braga", "Guimarães"]
  lang: string;           // "pt", "en", or "fr"
}
```

### **B. Recipe Schema (`content/recipes/`)**
```typescript
{
  title: string;
  prepTime: string;       // e.g., "30 min"
  difficulty: string;     // e.g., "Fácil"
  tags: string[];         // ["Vegan", "Sem Glúten", "Outono"]
  image: string;
  ingredientsList: string[]; // Simple array of strings
  featuredProducts: string[];// Array of Product IDs to link back to the Loja
  lang: string;
}
```

---

## 4. CORE FEATURES TO IMPLEMENT

### **Feature 1: Multi-Language Routing (i18n)**
*   The default route `/` redirects to `/pt/`.
*   The Navbar contains a minimalist language switcher: `PT | EN | FR`.
*   Clicking a language keeps you on the same page, just changes the locale folder.

### **Feature 2: The "Live" Instagram Footer**
*   Above the footer on every page, a full-width grid (6 columns on desktop, 3 on mobile) showing the latest Instagram posts.
*   *Dev Note:* The agent should use a lightweight script or a static fetch at build time to pull Instagram images via API, displaying them as `aspect-square` tiles with no gaps.

---

## 5. PAGE-BY-PAGE BLUEPRINT

### **1. Global Elements (On every page)**
*   **Header:** Transparent background that turns solid `#FBF9F6` on scroll. Left: Minimalist "Biobrassica" logo. Center: Navigation links. Right: Language switcher.
*   **Footer:** Dark Forest Green background (`#2C3F2D`), Cream text. Contains:
    *   Addresses for Braga & Guimarães.
    *   Accepted Payments icons (MBWay, Multibanco, Visa).
    *   Links to privacy/terms.

### **2. Homepage (`/pt/index.astro`)**
*   **Hero Section:** Full height (`100vh`). Background is a looping video of the farm. Large centered serif text: *"Do nosso solo, para a sua mesa."* (From our soil to your table). Small text below: *"Cultivo biológico em Braga & Guimarães."*
*   **Colheita da Semana (Harvest of the Week):** A 4-column grid pulling 4 products from the database where `isHighlight: true`.
*   **A Nossa Filosofia (Brief About):** 50/50 split layout. Left side: beautiful photo of dirty hands holding vegetables. Right side: Short text about organic farming + "Saber mais" button.
*   **Receita em Destaque:** One large featured recipe bridging the farm to the kitchen.

### **3. Quem Somos (`/pt/quem-somos.astro`)**
*   **Hero:** Large image of the founders/team.
*   **Timeline/Story:** Clean, vertical line layout detailing the journey from starting the farm to opening the shops.
*   **Values Grid:** 3 elegant icons (Earth, Community, Health) with short paragraphs.

### **4. Agricultura Biológica (`/pt/agricultura-bio.astro`)**
*   **Educational Focus:** Text-heavy but highly legible.
*   **Certifications:** High-resolution icons of your biological certifications (e.g., Certiplanet, Euro Leaf) with explanations of what they mean for the soil and the consumer.
*   **Seasonal Calendar:** A beautiful, static 12-month grid showing what is in season in Northern Portugal.

### **5. A Nossa Loja / The Catalog (`/pt/loja/index.astro`)**
*   **Header Alert:** A prominent, elegant banner at the top: *"A nossa montra digital. Reserve online, levante na loja de Braga ou Guimarães."* (Digital vitrine. Reserve online, pick up in Braga/Guimarães).
*   **Sidebar/Top Bar Filters:** Links to filter by "Frescos", "Mercearia", "Suplementos".
*   **Product Grid:** Clean cards. Image, Title, Price, Location Badges (e.g., `📍Braga & Guimarães`), and the "Reservar" WhatsApp button.

### **6. Receitas (`/pt/receitas/index.astro` & Single Page)**
*   **Index:** Masonry grid of recipes. Filterable by tags.
*   **Single Recipe Page:**
    *   Large hero image.
    *   Two columns: Left side (Ingredients), Right side (Step-by-step instructions).
    *   **The Bridge:** At the bottom, a section: *"Ingredientes da Loja"* showing the product cards for the bio ingredients used in the recipe, linking back to the WhatsApp reservation.

### **7. Contactos & Onde Estamos (`/pt/contactos.astro`)**
*   **Two-Column Store Layout:**
    *   **Store 1 (Braga):** Photo of the storefront. Address. Open hours. A clickable phone number. A Google Maps iframe.
    *   **Store 2 (Guimarães):** Same structure.
    **Whatsapp Contact**

## 6. DOCKER & DEPLOYMENT ARCHITECTURE
The agent must generate the necessary Docker files to allow for immediate local development with hot-reloading, as well as a production-ready container.

*   **`.dockerignore`:** Exclude `node_modules`, `dist`, `.astro`, and `.git`.
*   **`Dockerfile` (Multi-stage):**
    *   **Stage 1 (Builder):** Use `node:20-alpine` to install dependencies and run `npm run build`.
    *   **Stage 2 (Production):** Use a lightweight `nginx:alpine` image. Copy the generated static files from Astro's `dist/` folder into Nginx's public html directory. Expose port 80. (This makes the site incredibly fast and cheap to host).
*   **`docker-compose.yml`:**
    *   **Dev Service:** Map the local directory to `/app` inside the container, use a Node image, run `npm run dev -- --host`, and expose Astro's default port `4321`. This ensures hot-reloading works instantly on the host machine.
    *   **Prod Service:** Build using the `Dockerfile` and expose port `8080:80` to test the compiled production site locally.
