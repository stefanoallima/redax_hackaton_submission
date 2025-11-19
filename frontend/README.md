# Frontend Web App - redaxai.app

Next.js web application for legal research and user dashboard.

## Structure

```
/app
  /(auth)         # Auth pages (login, register)
  /dashboard      # User dashboard
  /research       # Legal search
  /pricing        # Pricing page
  layout.tsx      # Root layout
  page.tsx        # Homepage
/components       # Reusable UI components
/lib              # Utils, API client
/public           # Static assets
```

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure `.env.local` (see `.env.example`)

3. Run development server:
   ```bash
   npm run dev
   ```

4. Open http://localhost:3000

## Build

```bash
npm run build
npm run start
```

## Testing

```bash
npm run test        # Vitest unit tests
npm run test:e2e    # Cypress E2E tests
```

## Phase 0 Tasks
- [x] 0.1 Repository Setup
- [ ] 0.9 Web Frontend Scaffold
