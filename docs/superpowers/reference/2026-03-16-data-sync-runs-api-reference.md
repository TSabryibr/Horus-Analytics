# Data Sync Runs API Reference

Date: 2026-03-16
Audience: Frontend and backend developers consuming sync-run diagnostics
Document type: Reference
Status: Current for Phase 1 DP4

## Endpoint

- Method: `GET`
- Path: `/api/v1/data/sync/runs`
- Auth: API key required

## Purpose

This endpoint returns recent ingestion-run metadata plus derived diagnostics for:

- problem classification
- provider fallback classification
- filtered facet counts for the currently returned rows
- global summary counts for the unfiltered run window

The route is intended for operator-facing UI and diagnostics tooling.

## Query Parameters

### `limit`

- Type: integer
- Default: `50`
- Range: `1` to `500`
- Meaning: maximum number of recent runs loaded from metadata before any filters are applied

### `problems_only`

- Type: boolean
- Default: `false`
- Meaning: when `true`, only runs with a non-null `problem_type` are returned

### `fallback_type`

- Type: string
- Allowed values: `selection`, `runtime`
- Meaning:
  - `selection`: filter to runs with selection-time fallback
  - `runtime`: filter to runs with runtime ingest fallback
- Invalid value response: `400`

### `problem_type`

- Type: string
- Allowed values: `error`, `warning`, `selection_fallback`, `runtime_fallback`
- Meaning: filter to rows whose derived `problem_type` exactly matches the requested value
- Invalid value response: `400`

### `stage`

- Type: string
- Allowed values: `ingest_intraday`, `ingest_history`, `ingest_ticks`
- Normalization: trimmed and lowercased before validation
- Meaning: filter to one ingestion stage
- Invalid value response: `400`

### `provider`

- Type: string
- Allowed values: `AUTO`, `CSV`, `MUBASHER_DB`, `DIRECTFN`, `METASTOCK_DAT`
- Normalization: trimmed and uppercased before validation
- Meaning: filter to one persisted run provider
- Invalid value response: `400`

## Filter Semantics

All filters are additive.

Examples:

- `problems_only=true&problem_type=error`
- `problem_type=runtime_fallback&stage=ingest_history`
- `fallback_type=selection&provider=MUBASHER_DB`

Important:

- `limit` is applied first when loading runs from metadata storage
- all other filters are applied after that limited run set is loaded
- `summary` is computed over the limited run set before post-load filters
- `facets` are computed over the returned rows after filters

## Response Shape

Top-level keys:

- `runs`
- `summary`
- `facets`
- `filters`

### `runs`

Each row includes the persisted metadata from `data_engine.run_metadata.list_runs()`:

- `run_id`
- `stage`
- `provider`
- `realm`
- `stream`
- `started_at`
- `finished_at`
- `duration_ms`
- `status`
- `rows_read`
- `rows_written`
- `rows_rejected`
- `watermark_before`
- `watermark_after`
- `error`
- `provider_context`

Each row also includes derived operator fields:

- `problem_type`
  - `error`
  - `warning`
  - `runtime_fallback`
  - `selection_fallback`
  - `null`
- `has_selection_fallback`
- `has_runtime_fallback`
- `has_provider_fallback`
- `selection_fallback_from`
- `runtime_used_provider`
- `runtime_fallback_from`
- `runtime_failure_mode`
- `runtime_status`

### `summary`

Computed over the unfiltered run set loaded by `limit`.

Fields:

- `total_runs`
- `returned_runs`
- `error_runs`
- `warning_runs`
- `fallback_runs`
- `selection_fallback_runs`
- `runtime_fallback_runs`
- `problem_runs`
- `problem_type_counts`
- `stage_counts`
- `provider_counts`

`problem_type_counts` shape:

```json
{
  "error": 0,
  "warning": 0,
  "selection_fallback": 0,
  "runtime_fallback": 0
}
```

### `facets`

Computed over the currently returned rows after filters.

Fields:

- `problem_type_counts`
- `fallback_type_counts`
- `stage_counts`
- `provider_counts`

`fallback_type_counts` shape:

```json
{
  "selection": 0,
  "runtime": 0
}
```

### `filters`

Echoes the applied filter state:

- `problems_only`
- `fallback_type`
- `problem_type`
- `stage`
- `provider`

## Classification Rules

### `problem_type`

Priority order:

1. `error`
2. `warning`
3. `runtime_fallback`
4. `selection_fallback`
5. `null`

This means a run with `status=ERROR` is classified as `error` even if its provider context also contains fallback evidence.

### Selection vs runtime fallback

Selection fallback:

- derived from `provider_context.fallback_from`

Runtime fallback:

- derived from `provider_context.ingest_summary`
- usually indicated by `ingest_summary.fallback_from`
- also treated as runtime fallback when `ingest_summary.status == "completed_with_fallback"`

## Example Request

```http
GET /api/v1/data/sync/runs?problem_type=runtime_fallback&stage=ingest_history&provider=MUBASHER_DB
```

## Example Response Shape

```json
{
  "runs": [
    {
      "run_id": "abc123",
      "stage": "ingest_history",
      "provider": "MUBASHER_DB",
      "status": "COMPLETED",
      "problem_type": "runtime_fallback",
      "has_selection_fallback": false,
      "has_runtime_fallback": true,
      "has_provider_fallback": true,
      "selection_fallback_from": null,
      "runtime_used_provider": "CSV",
      "runtime_fallback_from": "MUBASHER_DB",
      "runtime_failure_mode": "source_unavailable",
      "runtime_status": "completed_with_fallback",
      "provider_context": {
        "reason": "explicit_provider_override",
        "fallback_from": null,
        "ingest_summary": {
          "used_provider": "CSV",
          "fallback_from": "MUBASHER_DB",
          "failure_mode": "source_unavailable",
          "status": "completed_with_fallback"
        }
      }
    }
  ],
  "summary": {
    "total_runs": 50,
    "returned_runs": 1,
    "error_runs": 3,
    "warning_runs": 5,
    "fallback_runs": 8,
    "selection_fallback_runs": 2,
    "runtime_fallback_runs": 6,
    "problem_runs": 12,
    "problem_type_counts": {
      "error": 3,
      "warning": 5,
      "selection_fallback": 2,
      "runtime_fallback": 2
    },
    "stage_counts": {
      "ingest_history": 20,
      "ingest_intraday": 20,
      "ingest_ticks": 10
    },
    "provider_counts": {
      "MUBASHER_DB": 25,
      "CSV": 15,
      "DIRECTFN": 10
    }
  },
  "facets": {
    "problem_type_counts": {
      "error": 0,
      "warning": 0,
      "selection_fallback": 0,
      "runtime_fallback": 1
    },
    "fallback_type_counts": {
      "selection": 0,
      "runtime": 1
    },
    "stage_counts": {
      "ingest_history": 1
    },
    "provider_counts": {
      "MUBASHER_DB": 1
    }
  },
  "filters": {
    "problems_only": false,
    "fallback_type": null,
    "problem_type": "runtime_fallback",
    "stage": "ingest_history",
    "provider": "MUBASHER_DB"
  }
}
```

## Error Responses

Invalid `fallback_type`:

```json
{"detail":"fallback_type must be 'selection' or 'runtime'"}
```

Invalid `problem_type`:

```json
{"detail":"problem_type must be 'error', 'warning', 'selection_fallback', or 'runtime_fallback'"}
```

Invalid `stage`:

```json
{"detail":"stage must be 'ingest_intraday', 'ingest_history', or 'ingest_ticks'"}
```

Invalid `provider`:

```json
{"detail":"provider must be 'AUTO', 'CSV', 'MUBASHER_DB', 'DIRECTFN', or 'METASTOCK_DAT'"}
```

## Notes for Consumers

- Use `summary` for the global view of the current run window.
- Use `facets` for live counts on the currently filtered result set.
- Use `problem_type` for UI badges and list grouping instead of recomputing classification from raw fields.
- Use `runtime_*` fields when you need the actual ingest fallback outcome, not just the originally selected provider.
