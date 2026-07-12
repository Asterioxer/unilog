# Frontend Architecture Reference Guide

This document defines the architecture, folder structure, data flow lifecycle, and design principles of the `unilog` React dashboard client.

---

## 1. Core Architecture Pattern

The dashboard follows a unidirectional data pipeline separating state stores, actions, network operations, and pure transformers:

```
User Trigger
     │
     ▼
useDashboardActions (Controller / Action Hook)
     │
     ▼
TanStack Query Mutations / Queries
     │
     ▼
apiClient / apiService (Network layer)
     │
     ▼
DashboardContext (State-Only Store)
     │
     ▼
Selectors / Transformers (Pure mappings)
     │
     ▼
Dashboard Content (Presentation layer)
```

---

## 2. Directory Structure

All frontend source assets are grouped by responsibility:
* **`context/`**: State providers containing context declarations. Houses zero business logic.
* **`hooks/`**: Custom hooks encapsulating async queries, mutations, keyboard controls, and task pollers.
* **`transformers/`**: Pure functions taking statistical inputs and converting them into chart-specific formats.
* **`types/`**: Strict TypeScript interfaces mapping backend models and frontend client state.
* **`services/`**: REST client setups and Query Keys directories.

---

## 3. Component Hierarchy

```
App
 └─ Dashboard (Wrapper)
     └─ DashboardProvider
         └─ DashboardContent (UI layout container)
             ├─ UploadPanel (File actions)
             ├─ MetadataPanel (Upload statistics)
             ├─ SummaryCard (Key metrics counters)
             └─ Recharts Views (Pie / Bars distribution charts)
```

---

## 4. State Lifecycle

The dashboard state matches the finite status lifecycle defined by `DashboardStatus`:

* **`idle`**: The initial dashboard state before any inputs are provided.
* **`uploading`**: Active file transfer state from client to backend. Exposes cancel capabilities and upload progress.
* **`processing`**: Synchronous analytics computation state for pasted logs or small files.
* **`polling`**: Asynchronous polling state querying task status for large files.
* **`ready`**: Successful completion state. Selctory properties map statistics data to visual charts.
* **`error`**: Processing, upload, or validation failure state. Renders recoverable alert banners.

---

## 5. Design Guidelines

1. **State Isolation**: Never embed mutation logic, API calls, or abort controllers directly inside context providers. Context files must remain purely data-oriented.
2. **Action Orchestration**: Consolidate actions inside `useDashboardActions`. Any operation mutating context state should be triggered from here.
3. **Pure Transformations**: Never transform API response formats directly inside presentation templates. Instead, write pure, testable functions in `transformers/` and consume them using `useMemo` hooks.
4. **Optimistic Updates**: Reset state instantly when starting a new operation to ensure a fast UI feel.
