# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Around the Grounds is a robust Python CLI tool for tracking food truck schedules and locations across multiple breweries. The project features:
- **Web interface** with mobile-responsive design and automatic deployment to Vercel
- **Async web scraping** with concurrent processing of multiple brewery websites
- **AI vision analysis** using Claude Vision API to extract vendor names from food truck logos/images
- **AI haiku generation** using Claude Sonnet with real-time weather integration to create contextual, poetic descriptions of daily food truck scenes
- **Auto-deployment** with git integration for seamless web updates
- **Extensible parser system** with custom parsers for different brewery website structures
- **Comprehensive error handling** with retry logic, isolation, and graceful degradation
- **Temporal workflow integration** with cloud deployment support (local, Temporal Cloud, custom servers)
- **Extensive test suite** with 196 tests covering unit, integration, vision analysis, haiku generation, and error scenarios
- **Modern Python tooling** with uv for dependency management and packaging

## Development Commands

### Environment Setup
```bash
uv sync --dev  # Install all dependencies including dev tools
```

### Running the Application
```bash
uv run around-the-grounds              # Run the CLI tool (~60s to scrape all sites)
uv run around-the-grounds --verbose    # Run with verbose logging (~60s)
uv run around-the-grounds --config /path/to/config.json  # Use custom config (~60s)
uv run around-the-grounds --preview    # Generate local preview files (~60s)
uv run around-the-grounds --deploy     # Run and deploy to web (~90s total)

# With AI features enabled (vision analysis + haiku generation)
export ANTHROPIC_API_KEY="your-api-key"
uv run around-the-grounds --verbose    # Run with AI features enabled (~60-90s)
uv run around-the-grounds --deploy     # Run with AI features and deploy to web (~90-60s)
```

**⏱️ Execution Times:** CLI operations typically take 60-90 seconds to scrape all brewery websites concurrently. Add extra time for AI features (vision analysis, haiku generation) and git operations when using `--deploy`.

### Local Preview & Testing

Before deploying, generate and test web files locally:

```bash
# Generate web files locally for testing (~60s to scrape all sites)
uv run around-the-grounds --preview

# Serve locally and view in browser
cd public && python -m http.server 8000
# Visit: http://localhost:8000

# Automated testing methods:
# Test data.json endpoint
cd public && timeout 10s python -m http.server 8000 > /dev/null 2>&1 & sleep 1 && curl -s http://localhost:8000/data.json | head -20 && pkill -f "python -m http.server" || true

# Test for specific event data (e.g., Sunday events)
cd public && timeout 10s python -m http.server 8000 > /dev/null 2>&1 & sleep 1 && curl -s http://localhost:8000/data.json | grep "2025-07-06" && pkill -f "python -m http.server" || true

# Test full homepage (basic connectivity)
cd public && timeout 10s python -m http.server 8000 > /dev/null 2>&1 & sleep 1 && curl -s http://localhost:8000/ > /dev/null && echo "✅ Homepage loads" && pkill -f "python -m http.server" || echo "❌ Homepage failed"

# Test JavaScript rendering (requires Node.js/puppeteer - optional)
# npm install -g puppeteer-cli
cd public && timeout 15s python -m http.server 8000 > /dev/null 2>&1 & sleep 2 && \
  node -e "
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({headless: true});
  const page = await browser.newPage();
  await page.goto('http://localhost:8000');
  await page.waitForSelector('.day-section', {timeout: 5000});
  const dayHeaders = await page.$$eval('.day-header', els => els.map(el => el.textContent));
  console.log('✅ Rendered days:', dayHeaders.slice(0,2).join(', '));
  const eventCount = await page.$$eval('.truck-item', els => els.length);
  console.log('✅ Rendered events:', eventCount);
  await browser.close();
})().catch(e => console.log('❌ JS render test failed:', e.message));
" && pkill -f "python -m http.server" || echo "❌ Install puppeteer for JS testing: npm install -g puppeteer"
```

**What `--preview` does:**
- Scrapes fresh data from all brewery websites
- Copies templates from `public_template/` to `public/`
- Generates `data.json` with current food truck data
- Creates complete website in `public/` directory (git-ignored)

This allows you to test web interface changes, verify data accuracy, and debug issues before deploying to production.


### Web Deployment

**IMPORTANT**: Web deployment requires GitHub App authentication setup. See [DEPLOYMENT.MD](./DEPLOYMENT.MD) for configuration details.

```bash
# Deploy fresh data to website (full workflow)
uv run around-the-grounds --deploy

# Deploy to custom repository
uv run around-the-grounds --deploy --git-repo https://github.com/username/repo.git

# Or use environment variable
export GIT_REPOSITORY_URL="https://github.com/username/repo.git"
uv run around-the-grounds --deploy

# This command will:
# 1. Scrape all brewery websites for fresh data
# 2. Copy web templates from public_template/ to target repository
# 3. Generate web-friendly JSON data in target repository
# 4. Authenticate using GitHub App credentials
# 5. Commit and push complete website to target repository
# 6. Trigger automatic deployment (Vercel/Netlify/etc.)
# 7. Website updates live within minutes

# For Temporal workflows
uv run around-the-grounds --deploy --verbose  # Recommended for scheduled runs
```

### Deployment
See [DEPLOYMENT.MD](./DEPLOYMENT.MD)

### Temporal Schedule Management
See [SCHEDULES.md](./SCHEDULES.md)

#### Schedule Features
- **Configurable intervals**: Any number of minutes (5, 30, 60, 120, etc.)
- **Multiple deployment modes**: Works with local, Temporal Cloud, and mTLS
- **Production ready**: Built-in error handling and detailed logging
- **Full lifecycle management**: Create, list, describe, pause, unpause, trigger, update, delete

### Testing
```bash
# Full test suite (196 tests)
uv run python -m pytest                    # Run all tests
uv run python -m pytest tests/unit/        # Unit tests only
uv run python -m pytest tests/parsers/     # Parser-specific tests
uv run python -m pytest tests/integration/ # Integration tests
uv run python -m pytest tests/unit/test_vision_analyzer.py  # Vision analysis tests
uv run python -m pytest tests/unit/test_haiku_generator.py  # Haiku generation tests
uv run python -m pytest tests/integration/test_vision_integration.py  # Vision integration tests
uv run python -m pytest tests/integration/test_haiku_integration.py   # Haiku integration tests
uv run python -m pytest tests/test_error_handling.py  # Error handling tests

# Test options
uv run python -m pytest -v                 # Verbose output
uv run python -m pytest --cov=around_the_grounds --cov-report=html  # Coverage
uv run python -m pytest -k "test_error"    # Run error-related tests
uv run python -m pytest -k "vision"        # Run vision-related tests
uv run python -m pytest -k "haiku"         # Run haiku-related tests
uv run python -m pytest -x                 # Stop on first failure
```

### Code Quality
```bash
uv run black .             # Format code
uv run isort .             # Sort imports
uv run flake8             # Lint code
uv run mypy around_the_grounds/  # Type checking
```

## Architecture

The project follows a modular architecture with clear separation of concerns:

```
around_the_grounds/
├── config/
│   ├── breweries.json          # Brewery configurations
│   └── settings.py             # Vision analysis and other settings
├── models/
│   ├── brewery.py              # Brewery data model  
│   └── schedule.py             # FoodTruckEvent data model
├── parsers/
│   ├── __init__.py             # Parser module exports
│   ├── base.py                 # Abstract base parser with error handling
│   ├── stoup_ballard.py        # Stoup Brewing parser
│   ├── bale_breaker.py         # Bale Breaker parser
│   ├── urban_family.py         # Urban Family parser with vision analysis
│   └── registry.py             # Parser registry/factory
├── scrapers/
│   └── coordinator.py          # Async scraping coordinator with error isolation
├── temporal/                   # Temporal workflow integration
│   ├── __init__.py             # Module initialization
│   ├── workflows.py            # FoodTruckWorkflow definition
│   ├── activities.py           # ScrapeActivities and DeploymentActivities
│   ├── config.py               # Temporal client configuration system
│   ├── schedule_manager.py     # Comprehensive schedule management script
│   ├── shared.py               # WorkflowParams and WorkflowResult data classes
│   ├── worker.py               # Production-ready worker with error handling
│   ├── starter.py              # CLI workflow execution client
│   └── README.md               # Temporal-specific documentation
├── utils/
│   ├── date_utils.py           # Date/time utilities with validation
│   ├── vision_analyzer.py      # AI vision analysis for vendor identification
│   ├── haiku_generator.py      # AI haiku generation with weather-grounded imagery
│   └── weather.py              # Real-time weather fetching via Open-Meteo API
└── main.py                     # CLI entry point with web deployment support

public_template/                # Web interface templates (copied to target repo)
├── index.html                  # Mobile-responsive web interface template
└── vercel.json                 # Vercel deployment configuration

public/                         # Generated files (git ignored)
└── data.json                   # Generated web data (not committed to source repo)

tests/                          # Comprehensive test suite
├── conftest.py                 # Shared test fixtures
├── fixtures/
│   ├── html/                   # Real HTML samples from brewery websites
│   └── config/                 # Test configurations
├── unit/                       # Unit tests for individual components
│   ├── test_vision_analyzer.py # Vision analysis component tests
│   └── test_haiku_generator.py # Haiku generation component tests
├── parsers/                    # Parser-specific tests
├── integration/                # End-to-end integration tests
│   ├── test_vision_integration.py  # Vision analysis integration tests
│   └── test_haiku_integration.py   # Haiku generation integration tests
└── test_error_handling.py      # Comprehensive error scenario tests
```

### Key Components

- **Models**: Data classes for breweries and food truck events with validation
- **Parsers**: Extensible parser system with robust error handling and validation
  - `BaseParser`: Abstract base with HTTP error handling, validation, and logging
  - `StoupBallardParser`: Handles structured HTML with date/time parsing
  - `BaleBreakerParser`: Handles limited data with Instagram fallbacks
  - `UrbanFamilyParser`: Hivey API integration with AI vision analysis fallback for vendor identification
- **Registry**: Dynamic parser registration and retrieval with error handling
- **Scrapers**: Async coordinator with concurrent processing, retry logic, and error isolation
- **Temporal**: Workflow orchestration for reliable execution and scheduling
  - `FoodTruckWorkflow`: Main workflow orchestrating scraping and deployment
  - `ScrapeActivities`: Activities wrapping existing scraping functionality
  - `DeploymentActivities`: Activities for web data generation and git operations
  - `FoodTruckWorker`: Production-ready worker with thread pool and signal handling
  - `FoodTruckStarter`: CLI client for manual workflow execution
  - `ScheduleManager`: Comprehensive schedule management with configurable intervals and full lifecycle operations
- **Config**: JSON-based configuration with validation and error reporting
- **Utils**: Date/time utilities, AI vision analysis for vendor identification, AI haiku generation with weather integration, real-time weather fetching via Open-Meteo API
- **Web Interface**: Mobile-responsive HTML/CSS/JS frontend with automatic data fetching
- **Web Deployment**: Git-based deployment system with Vercel integration for automatic updates
- **Tests**: 196 tests covering all scenarios including extensive error handling, vision analysis, and haiku generation

### Core Dependencies

**Production:**
- `aiohttp` - Async HTTP client for web scraping with timeout handling
- `beautifulsoup4` - HTML parsing with error tolerance
- `lxml` - Fast XML/HTML parser backend
- `requests` - HTTP library (legacy support)
- `anthropic` - Claude API for AI-powered image analysis and haiku generation
- `temporalio` - Temporal Python SDK for workflow orchestration

**Development & Testing:**
- `pytest` - Test framework with async support
- `pytest-asyncio` - Async test support
- `aioresponses` - HTTP response mocking for tests
- `pytest-mock` - Advanced mocking capabilities
- `freezegun` - Time mocking for date-sensitive tests
- `pytest-cov` - Code coverage reporting

The CLI is configured in `pyproject.toml` with entry point `around-the-grounds = "around_the_grounds.main:main"`.

## Adding New Breweries

See [ADDING-BREWERIES.md](./ADDING-BREWERIES.md)

## Haiku Generator

The system includes AI-powered haiku generation (using `claude-sonnet-4-6` at `temperature=0.85`) that creates contextual, poetic descriptions of daily food truck scenes. Haikus are grounded in real-time weather data fetched from the Open-Meteo API (free, no API key required) for Ballard, Seattle. Weather data is required -- if the weather fetch fails, no haiku is generated.

**Time-based weather logic** selects the appropriate forecast based on current Pacific Time:
- Before 6pm PT: uses afternoon forecast for today
- 6-9pm PT: uses evening forecast for today
- 9pm-midnight PT: uses afternoon forecast for tomorrow
- After midnight: uses afternoon forecast for today (new calendar day)

Haiku prompts incorporate weather-grounded imagery, time-of-day awareness, and beer/brewery references while avoiding invented sensory details.

See [HAIKU-GENERATOR.md](./HAIKU-GENERATOR.md) for detailed documentation on configuration, usage, and implementation.

## AI Vision Analysis

The system includes AI-powered vision analysis to extract food truck vendor names from logos and images when text-based methods fail. The analyzer uses Claude Vision API as a fallback, with retry logic and graceful degradation.

See [VISION-ANALYSIS.md](./VISION-ANALYSIS.md) for detailed documentation on configuration, usage, and implementation.

## Error Handling Strategy

The application implements comprehensive error handling with error isolation, graceful degradation, and selective retry logic.

See [ERROR-HANDLING.md](./ERROR-HANDLING.md) for the complete error handling strategy guide.

## Code Standards

- **Line length**: 88 characters (Black formatting)
- **Type hints**: Required throughout (`mypy` with `disallow_untyped_defs = true`)
- **Python compatibility**: 3.8+ required
- **Import sorting**: Black profile via isort
- **Async patterns**: async/await for all I/O operations
- **Error handling**: Comprehensive error handling and logging required
- **Testing**: All new code must include unit tests and error scenario tests
- **Logging**: Use class loggers (`self.logger`) with appropriate levels

## Testing Strategy

The project includes a comprehensive test suite with 196 tests covering unit, integration, vision analysis, haiku generation, and error scenarios.

See [TESTING.md](./TESTING.md) for the complete testing strategy and guide.

## Development Workflow

When working on this project:

1. **Run tests first** to ensure current functionality works
2. **Write failing tests** for new features before implementation
3. **Implement with error handling** - always include try/catch and logging
4. **Test error scenarios** - network failures, invalid data, timeouts
5. **Preview changes locally** using `--preview` flag before deployment
6. **Run full test suite** before committing changes
7. **Update documentation** if adding new parsers or changing architecture

### Local Development Workflow
```bash
# 1. Make code changes
# 2. Test locally with preview
uv run around-the-grounds --preview
cd public && python -m http.server 8000

# 3. Run tests
uv run python -m pytest

# 4. Deploy when ready
uv run around-the-grounds --deploy
```

## Web Deployment Workflow

See [WEB-DEPLOYMENT.md](./WEB-DEPLOYMENT.md) for the complete web deployment workflow guide.

## Type Annotations

The project uses strict type checking with MyPy (`disallow_untyped_defs = true`) and Pylance.

See [TYPE-ANNOTATIONS.md](./TYPE-ANNOTATIONS.md) for the comprehensive type annotation maintenance guide.

## Troubleshooting Common Issues

- **Parser not found**: Check `parsers/registry.py` registration
- **Network timeouts**: Adjust timeout in `ScraperCoordinator` constructor
- **Date parsing issues**: Check `utils/date_utils.py` patterns and add new formats
- **Test failures**: Use `pytest -v -s` for detailed output and debug prints
- **Import errors**: Ensure `__init__.py` files are present and imports are correct