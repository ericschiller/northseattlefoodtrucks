# North Seattle Beer

A Python CLI tool for tracking food truck schedules and brewery events across North Seattle. Scrapes brewery websites asynchronously and generates a unified 7-day schedule served via a Nuxt 3 web frontend.

## Features

- **Async Web Scraping**: Concurrent processing of multiple brewery websites
- **Events Tab**: Separates food trucks from other brewery events (trivia, live music, community events)
- **AI Vision Analysis**: Extracts vendor names from food truck images using Claude Vision API
- **Auto-Deployment**: Git-based deployment to static site platforms (Vercel, Netlify, etc.)
- **Temporal Workflows**: Reliable scheduling with cloud or local execution
- **Comprehensive Testing**: Tests covering unit, integration, and error scenarios

## How It Works

This repository contains the **scraping and scheduling engine**. When run with `--deploy`, it:

1. **Scrapes** brewery websites for food truck and event schedules
2. **Generates** static site data (`data.json`) in `frontend/public/`
3. **Pushes** the updated frontend to a target repository for automatic deployment

**Two-Repository Architecture:**
- **Source repo** (this one): Contains scraping code, Nuxt frontend, and web templates
- **Target repo**: Receives the built site, served as a static site

## Quick Start

### Installation
```bash
git clone <this-repo>
cd northseattlebeer
uv sync
```

### Basic CLI Usage
```bash
uv run around-the-grounds              # Show 7-day schedule
uv run around-the-grounds --verbose    # With detailed logging
uv run around-the-grounds --preview    # Generate local preview files
uv run around-the-grounds --deploy     # Scrape and deploy to web
```

## Local Preview & Testing

```bash
# 1. Generate web data locally
uv run around-the-grounds --preview

# 2. Run the Nuxt development server
cd frontend
npm install
npm run dev
# Visit: http://localhost:3000
```

**What `--preview` does:**
1. Scrapes fresh data from all brewery websites
2. Generates `data.json` in `frontend/public/` with `truck_events` and `other_events` arrays

## Web Deployment

To deploy a live website, you need a **target repository** and **GitHub App** for authentication. See [DEPLOYMENT.MD](./DEPLOYMENT.MD) for full setup.

### Environment Variables
```bash
# Optional: AI vision analysis
ANTHROPIC_API_KEY=your-anthropic-api-key

# Required for web deployment
GITHUB_APP_ID=123456
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_APP_PRIVATE_KEY_B64=base64-encoded-private-key
GIT_REPOSITORY_URL=https://github.com/username/target-repo.git
```

## Scheduled Updates

Use **Temporal workflows** to run automatic updates with a persistent worker system.

```bash
# Start worker (runs continuously)
uv run python -m around_the_grounds.temporal.worker

# Create schedule (runs every 30 minutes)
uv run python -m around_the_grounds.temporal.schedule_manager create --schedule-id daily-scrape --interval 30

# List / pause / trigger / delete schedules
uv run python -m around_the_grounds.temporal.schedule_manager list
uv run python -m around_the_grounds.temporal.schedule_manager trigger --schedule-id daily-scrape
uv run python -m around_the_grounds.temporal.schedule_manager delete --schedule-id daily-scrape
```

See [SCHEDULES.md](./SCHEDULES.md) for full schedule management documentation.

## Configuration

### Supported Breweries / Sources

| Brewery | Parser | Notes |
|---|---|---|
| Chuck's Hop Shop Greenwood | CSV (Google Sheets) | Food trucks + events |
| Broadview Tap House | Seattle Food Truck API | Food trucks |
| Broadview Tap House | Google Calendar iCal | Events (live music, trivia, etc.) |
| Ridgecrest Public House | Squarespace Events | Food trucks + events |
| Halcyon Brewing Co. | Squarespace Events | Events (Bingo, Trivia, Coloring Night) |
| Shoreline Community College | WA Food Trucks | Food trucks |
| Hellbent Brewing Company | SimCal (WordPress) | Food trucks |
| Ravenna Brewing Co. | Squarespace Events | Food trucks + events |

### Adding New Breweries
1. Create parser class in `around_the_grounds/parsers/`
2. Register parser in `around_the_grounds/parsers/registry.py`
3. Add brewery config to `around_the_grounds/config/breweries.json`
4. Write tests in `tests/parsers/`

See [ADDING-BREWERIES.md](./ADDING-BREWERIES.md) for detailed instructions.

### Event Categories

Scraped events are assigned a `category` field:

| Category | Description |
|---|---|
| `food-truck` | Food truck bookings |
| `trivia` | Trivia nights |
| `live-music` | Live music events |
| `community` | Bingo, run clubs, knitting groups, and other recurring community events |

The frontend splits events into a **TRUCKS** tab and an **EVENTS** tab based on this field.

## Development

### Setup
```bash
uv sync --dev
```

### Local Workflow
```bash
uv run around-the-grounds --preview    # Scrape + generate data.json
cd frontend && npm run dev             # Run Nuxt dev server
uv run python -m pytest                # Run tests
```

### Code Quality
```bash
uv run black .
uv run flake8
uv run mypy around_the_grounds/
```

## Architecture

- **CLI**: `around_the_grounds/main.py` — entry point, produces `truck_events`/`other_events` split in `data.json`
- **Parsers**: Extensible system supporting HTML, CSV, JSON APIs, Squarespace, SimCal, iCal, Google Calendar
- **Scrapers**: Async coordinator with error handling and retries
- **AI Utils**: Claude Vision API for vendor name extraction from images
- **Temporal**: Workflow orchestration for reliable scheduling
- **Frontend**: Nuxt 3 app in `frontend/` with TRUCKS / EVENTS tab toggle, Slate Blue and Teal theme

### Frontend

The `frontend/` directory is a Nuxt 3 app:

```
frontend/
├── app.vue                  # Root component with Slate Blue theme, tab toggle, and past-event filtering
├── components/
│   ├── AppHeader.vue        # Site header with Slate Blue title and last-updated date
│   ├── AppFooter.vue        # Site footer with matching theme
│   ├── DaySection.vue       # Day group with Teal-highlighted headers and event count
│   └── TruckItem.vue        # Individual event card with subtle shadow and Sage Green tags
├── public/
│   └── data.json            # Generated by --preview or --deploy (git-ignored)
└── package.json
```

```bash
# Run frontend dev server (after generating data.json)
cd frontend
npm install
npm run dev
```

## Requirements

- Python 3.8+
- Node.js (for frontend)
- Dependencies: `aiohttp`, `beautifulsoup4`, `temporalio`, `anthropic` (optional for AI features)

## License

MIT License
