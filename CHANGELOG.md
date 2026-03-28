# CHANGELOG.md

## 23:56 (FINAL)

### Features Added
- **Async Job Polling Architecture**: Implemented full backend job state management with real-time progress tracking (HTTP 202 responses, background workers, 1.5s polling loops)
- **Live Screen Data Integration**: Wired all dashboard screens (Ingest, Detection, Evidence, Legal) to backend APIs with real-time updates
- **Integration Test Suite Enabled**: Removed skip gates, fixed interactive input handling, all 4 integration tests now pass alongside 9 unit tests
- **Backend Job CRUD Helpers**: Added `create_job()`, `get_job()`, `update_job()`, `request_job_cancel()`, job stats tracking
- **Frontend Job Polling Loop**: Ingest benchmark now polls `/jobs/<id>` every 1.5s with automatic progress card updates and 12-minute timeout
- **Live System Status**: Health check and metrics endpoints return active job counters instead of hardcoded values

### Files Modified
- `backend/api/main.py` – Job helpers (lines 114–237), route changes for /analysis/piracy-benchmark/async, /jobs/<id>, /jobs/<id>/cancel
- `frontend/src/types.ts` – Added BenchmarkJobStartResponse, BenchmarkJobProgressData, BenchmarkJobStatusResponse types
- `frontend/src/services/api.ts` – Added fetchBenchmarkJob() function, updated runPiracyBenchmark() return type
- `frontend/src/pages/IngestPage.tsx` – Replaced simulated progress with real job polling (lines 346–423)
- `backend/tests/test_sentinel.py` – Removed RUN_SENTINEL_INTEGRATION skip gate, made interactive inputs non-blocking
- `test_progress.py` – Wrapped executable logic in main() guard to prevent pytest collection hangs
- `tests/test_bias_tuning.py` – Fixed import path, changed assertions to directional comparisons
- `frontend/src/components/` – Updated DetectionFeed, StatCard, UploadBox for live data display
- `frontend/src/pages/DetectionPage.tsx`, `EvidencePage.tsx`, `LegalPage.tsx` – Integrated live API endpoints

### Issues Faced
- **Benchmark workflow hung at 75%**: Frontend simulated progress interval stopped before job completion. Solution: Replaced with real backend job polling.
- **Integration tests skipped by default**: RUN_SENTINEL_INTEGRATION env var blocking tests. Solution: Removed skip gates, integrated tests now enabled by default.
- **Interactive video selection blocked pytest**: test_dual_engine_primary called input() during pytest capture. Solution: Added TTY check, auto-select first video in non-interactive context.
- **Pytest collection crashes**: test_progress.py executed network calls on import. Solution: Wrapped in main() guard with __name__ check.
- **Async job endpoints missing**: Backend had no /jobs routes, frontend couldn't poll. Solution: Implemented full CRUD helpers and Flask routes.
- **Bias test assertions too strict**: Assumed fixed threshold on ML output. Solution: Changed to directional comparisons (conservative lowers, aggressive raises).

## 00:07

### Features Added
- **Modern Slate Design System**: Implemented a comprehensive UI/UX overhaul across all primary dashboard pages (Ingest, Detection, Evidence, Legal).
- **Typography Standardized**: Transitioned to Google Fonts — Inter (body), Outfit (display), and JetBrains Mono (coding/status).
- **Refined Glassmorphism**: Enhanced all panel and card styles with higher blur, subtle borders, and consistent transparency for a premium feel.
- **Improved Data Visualization**: Modernized `StatCard` and `ChartPanel` components with cleaner layouts and hover effects.
- **Responsive Navigation**: Updated `Sidebar` and `Topbar` with improved spacing and high-fidelity branding.

### Files Modified
- `frontend/src/index.css`
- `frontend/src/layouts/AppLayout.tsx`
- `frontend/src/components/Sidebar.tsx`
- `frontend/src/components/Topbar.tsx`
- `frontend/src/components/UploadBox.tsx`
- `frontend/src/components/StatCard.tsx`
- `frontend/src/components/ChartPanel.tsx`
- `frontend/src/components/DetectionFeed.tsx`
- `frontend/src/pages/IngestPage.tsx`
- `frontend/src/pages/DetectionPage.tsx`
- `frontend/src/pages/EvidencePage.tsx`
- `frontend/src/pages/LegalPage.tsx`

### Issues Faced
- **JSX Syntax Regressions**: Encountered and resolved nested element errors in `IngestPage.tsx` during modernization.
- **RECHART Alignment**: Adjusted chart margins and tooltips to align with the higher padding of the new glass containers.
