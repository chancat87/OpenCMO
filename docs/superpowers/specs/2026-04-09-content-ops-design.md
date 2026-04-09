# Content Ops Layer Design

## Goal

Add a compatible content-operations layer to OpenCMO so Blog/SEO work becomes a first-class workflow instead of a one-shot generation request.

The target outcome is:

- stronger, more consistent Blog/SEO output quality
- clearer next-action recommendations for users
- reusable intermediate artifacts across agents and channels
- a persistent content memory layer that improves future recommendations

This design upgrades OpenCMO from:

- monitoring + insight generation
- one-off content generation

to:

- research-backed content execution
- prioritized content backlog management
- content graph intelligence with long-term memory

## Scope

Phase 1 covers Blog/SEO content only.

The new workflow must support:

- research brief generation
- content plan generation
- draft generation
- review and revision loop
- opportunity queue for Blog/SEO work
- content graph nodes and edges for approved content
- project-page-first UX, with chat as a compatible trigger

## Non-Goals

This design does not, in Phase 1:

- redesign non-Blog social channel generation
- replace existing monitoring pipelines
- replace existing campaign storage
- introduce an external queue or worker runtime
- build a separate content application outside the current project pages
- fully automate publishing to CMSes in the first iteration

## Why This Is Worth Doing

OpenCMO already has meaningful pieces of the future system:

- `generate_research_brief()` and campaign artifacts
- opportunity snapshots built from monitoring data
- knowledge graph and graph expansion
- project pages, campaigns pages, and task runtime

What is missing is the operational chain that connects these pieces:

- monitoring signals do not become a durable content backlog
- content generation does not consistently flow through shared research context
- generated content does not write itself back into the graph as long-term memory
- users cannot yet work through a visible Blog/SEO execution loop from project pages

This design closes those gaps.

## Current State

### Strengths already present

- `src/opencmo/tools/research_brief.py` already creates shared campaign context and stores artifacts.
- `src/opencmo/opportunities.py` already computes useful opportunity summaries and cluster signals.
- `src/opencmo/context.py` already combines monitoring, graph, competitor, and brand-kit context.
- `src/opencmo/storage/campaigns.py` already persists campaign runs and artifacts.
- `src/opencmo/storage/graph.py` already persists graph expansion state and graph-compatible nodes/links.
- Project pages, graph pages, and campaign routes already exist in the frontend and backend.

### Gaps to close

- No dedicated Blog/SEO pipeline from brief to plan to draft to review.
- No durable `content_opportunities` backlog with workflow state.
- No content nodes in the graph, only brand, keyword, competitor, SERP, and discussion entities.
- No project-page workflow card that lets users act on a content opportunity immediately.
- Chat can generate content, but there is no shared visible execution state for content work.

## Recommended Approach

Introduce a `Content Ops` layer that sits on top of existing campaigns, artifacts, graph, insights, and background tasks.

Canonical flow:

`Project + Monitoring Signals`
-> `Research Brief Service`
-> `Content Pipeline Service`
-> `Opportunity Queue Service`
-> `Content Graph Service`

This is a compatible evolution, not a rewrite.

## Architecture

### 1. Research Brief Service

Responsibilities:

- gather project, graph, monitoring, and brand context
- gather opportunity context when work starts from a queue item
- create a standardized Blog/SEO brief
- persist the brief as a campaign artifact

Outputs:

- `content_brief`
- `opportunity_snapshot`

### 2. Content Pipeline Service

Responsibilities:

- generate a structured content plan from the brief
- generate a draft from the plan
- run reviewer passes
- request or generate revisions
- expose a single content-run view to the UI

Outputs:

- `content_plan`
- `content_draft`
- `content_review`
- `content_revision`

### 3. Opportunity Queue Service

Responsibilities:

- refresh durable content opportunities from monitoring + graph data
- prioritize opportunities for Blog/SEO work
- track whether each opportunity is open, planned, active, or completed

Outputs:

- durable backlog rows
- project-page queue cards

### 4. Content Graph Service

Responsibilities:

- create content nodes for approved work
- map content into clusters
- record internal-link and refresh relationships
- feed graph intelligence back into future briefs and queue ranking

Outputs:

- `content_nodes`
- `content_edges`

## Data Model

### Reuse existing tables

These stay in place:

- `campaign_runs`
- `campaign_artifacts`
- `insights`
- `graph_expansions`
- `graph_expansion_nodes`
- `graph_expansion_edges`

Phase 1 should treat campaign artifacts as the storage layer for intermediate workflow state.

### New artifact types

Use explicit artifact types under `campaign_artifacts.artifact_type`:

- `content_brief`
- `content_plan`
- `content_draft`
- `content_review`
- `content_revision`
- `opportunity_snapshot`
- `content_publish_packet`

These make the pipeline legible in campaigns UI without forcing a large schema migration.

### New table: `content_opportunities`

Purpose:

- persistent Blog/SEO backlog
- status tracking across runs
- project-page action source

Proposed columns:

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `project_id INTEGER NOT NULL REFERENCES projects(id)`
- `opportunity_type TEXT NOT NULL`
- `status TEXT NOT NULL DEFAULT 'open'`
- `title TEXT NOT NULL`
- `summary TEXT NOT NULL`
- `priority TEXT NOT NULL DEFAULT 'medium'`
- `score INTEGER NOT NULL DEFAULT 0`
- `target_keyword TEXT`
- `target_url TEXT`
- `recommended_action TEXT NOT NULL DEFAULT ''`
- `source_payload_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL DEFAULT (datetime('now'))`
- `updated_at TEXT NOT NULL DEFAULT (datetime('now'))`
- `resolved_at TEXT`

Recommended indexes:

- `(project_id, status, score DESC, created_at DESC)`
- `(project_id, opportunity_type, status)`

### New table: `content_nodes`

Purpose:

- persist content assets as graph entities
- provide durable linkage between runs, artifacts, and long-term content memory

Proposed columns:

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `project_id INTEGER NOT NULL REFERENCES projects(id)`
- `run_id INTEGER REFERENCES campaign_runs(id)`
- `artifact_id INTEGER REFERENCES campaign_artifacts(id)`
- `content_type TEXT NOT NULL`
- `title TEXT NOT NULL`
- `slug TEXT NOT NULL DEFAULT ''`
- `primary_keyword TEXT NOT NULL DEFAULT ''`
- `intent_type TEXT NOT NULL DEFAULT ''`
- `status TEXT NOT NULL DEFAULT 'planned'`
- `refresh_priority INTEGER NOT NULL DEFAULT 0`
- `canonical_url TEXT`
- `meta_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL DEFAULT (datetime('now'))`
- `updated_at TEXT NOT NULL DEFAULT (datetime('now'))`

Recommended indexes:

- `(project_id, status, updated_at DESC)`
- `(project_id, primary_keyword)`
- unique optional index on `(project_id, slug)` when slug exists

### New table: `content_edges`

Purpose:

- store content graph relationships separately from expansion-discovery edges

Proposed columns:

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `project_id INTEGER NOT NULL REFERENCES projects(id)`
- `source_content_id INTEGER NOT NULL REFERENCES content_nodes(id)`
- `target_content_id INTEGER NOT NULL REFERENCES content_nodes(id)`
- `relation_type TEXT NOT NULL`
- `meta_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL DEFAULT (datetime('now'))`

Relation types for Phase 1:

- `internal_link_to`
- `same_cluster`
- `supports_cluster`
- `refreshes`
- `targets_keyword_gap`
- `competes_with`

## Workflow

### Entry points

Primary entry:

- project page

Secondary compatible entry:

- chat request for Blog/SEO content

Chat does not get a separate workflow. It triggers the same content run and points users to the project page for the full artifact view.

### Canonical content run

1. User selects an opportunity or starts a manual Blog/SEO topic.
2. System creates a content run under `campaign_runs`.
3. System builds and stores `content_brief`.
4. System builds and stores `content_plan`.
5. System generates and stores `content_draft`.
6. System runs reviewers and stores `content_review` artifacts.
7. If blocking issues exist, system marks the run as `needs_revision`.
8. User or system triggers a revision pass, storing `content_revision`.
9. On approval, system syncs content memory into `content_nodes` and `content_edges`.
10. Related `content_opportunities` row is updated to `planned` or `completed`.

## Content Brief Contract

Inputs:

- `project_id`
- `opportunity_id` or manual `topic`

Brief contents:

- project identity and category
- target audience, pain, promise, proof
- relevant competitors
- tracked keywords and ranking state
- GEO / SEO / community signals
- cluster gaps and top opportunities
- target page type recommendation
- target keyword and supporting keywords
- differentiated angle to avoid generic SERP-matching output
- source evidence references

This brief becomes the standard input for all downstream Blog/SEO generation.

## Content Plan Contract

The plan must be structured, not just a prose outline.

Required fields:

- `topic`
- `page_type`
- `intent_type`
- `target_keyword`
- `secondary_keywords`
- `title_candidates`
- `recommended_outline`
- `evidence_to_include`
- `internal_links_to_include`
- `cta_angle`
- `differentiator_angle`
- `snippet_opportunities`

The user should see this plan before or alongside draft generation.

## Draft Contract

The draft must be generated from the plan, not directly from a loose topic prompt.

Rules:

- preserve the selected target keyword and intent
- carry forward the differentiator angle from the brief
- explicitly use evidence slots from the plan
- include internal-link targets from the plan
- remain useful as standalone content, not just product promotion

## Review Loop

Phase 1 reviewer set:

- `seo reviewer`
- `editorial reviewer`
- `conversion reviewer`

Severity classes:

- `blocking`
- `important`
- `polish`

Only `blocking` and `important` findings should automatically trigger revision behavior.

Review output should include:

- issue summary
- why it matters
- suggested revision direction
- confidence

## Opportunity Queue

The queue is a durable backlog, not a transient summary.

Each opportunity must answer:

- why this should be done now
- what the user should create or update
- what the target keyword or target URL is
- what expected gain the work could influence

Opportunity types for Phase 1:

- `quick_win`
- `refresh`
- `cluster_gap`
- `competitor_gap`
- `ctr_fix`
- `new_page`

## Content Graph Layer

Phase 1 content graph adds content assets to the current graph.

New node types:

- `blog_post`
- `pillar_page`
- `comparison_page`
- `integration_page`
- `glossary_page`
- `refresh_candidate`

New edge types:

- `internal_link_to`
- `same_cluster`
- `supports_cluster`
- `refreshes`
- `targets_keyword_gap`
- `competes_with`

Graph display rule for Phase 1:

- show approved or active content nodes only
- do not render every draft artifact as a graph node

## Backend Changes

### New services

Add:

- `src/opencmo/services/content_brief_service.py`
- `src/opencmo/services/content_pipeline_service.py`
- `src/opencmo/services/content_queue_service.py`
- `src/opencmo/services/content_graph_service.py`

### New storage module

Add:

- `src/opencmo/storage/content_ops.py`

Responsibilities:

- CRUD for `content_opportunities`
- CRUD for `content_nodes`
- CRUD for `content_edges`

### New background task kinds

Add task kinds:

- `content_brief`
- `content_pipeline`
- `content_graph_sync`

Add executors:

- `src/opencmo/background/executors/content_brief.py`
- `src/opencmo/background/executors/content_pipeline.py`
- `src/opencmo/background/executors/content_graph.py`

This keeps long-running LLM work out of synchronous request handlers.

## API Design

Add a new router:

- `src/opencmo/web/routers/content_ops.py`

Proposed endpoints:

- `GET /api/v1/projects/{project_id}/content-opportunities`
- `POST /api/v1/projects/{project_id}/content-opportunities/refresh`
- `POST /api/v1/projects/{project_id}/content-runs`
- `GET /api/v1/content-runs/{run_id}`
- `POST /api/v1/content-runs/{run_id}/revise`
- `POST /api/v1/content-runs/{run_id}/approve`
- `GET /api/v1/projects/{project_id}/content-graph`

Campaign routes remain compatible. The new routes provide richer workflow state rather than replacing existing campaign APIs.

## Frontend Design

### Primary page

Use the project page as the main content-ops workbench.

Target file:

- `frontend/src/pages/ProjectPage.tsx`

Add these blocks:

- `ContentOpportunityPanel`
- `ContentRunPanel`

Suggested placement:

- below `ActionFeed`
- above `ScorePanel`

### Campaign artifact rendering

Extend campaign detail views so artifacts render semantically:

- brief card
- plan card
- draft markdown viewer
- review findings panel
- revision timeline

### Graph page extension

Target file:

- `frontend/src/pages/GraphPage.tsx`

Extend graph rendering to show approved content nodes and content relationships.

### New frontend components

Suggested files:

- `frontend/src/components/content/ContentOpportunityPanel.tsx`
- `frontend/src/components/content/ContentRunPanel.tsx`
- `frontend/src/components/content/ContentBriefCard.tsx`
- `frontend/src/components/content/ContentPlanCard.tsx`
- `frontend/src/components/content/ContentDraftViewer.tsx`
- `frontend/src/components/content/ContentReviewPanel.tsx`
- `frontend/src/components/content/ContentRevisionTimeline.tsx`

### Chat compatibility

When a user starts Blog/SEO generation from chat:

- create a content run
- return phase status in chat
- link or refer the user to the project page for the full workflow view

## Error Handling

### Brief generation failure

- run status becomes `failed`
- preserve any fetched opportunity snapshot
- show actionable retry affordance

### Partial pipeline failure

- if plan succeeds but draft fails, keep the successful artifacts
- if draft succeeds but review fails, preserve the draft and mark reviewer status separately

### Reviewer disagreement

- persist all reviewer outputs
- only auto-block on `blocking` severity
- do not discard a draft because one reviewer is noisy

### Graph sync failure

- approval of the content run should remain visible
- graph sync can retry asynchronously
- do not lose the approved draft due to graph persistence failure

## Phasing

### Phase 1A: Content Run Backbone

Deliver:

- brief generation
- plan generation
- draft generation
- review loop
- content-run APIs
- project-page run panel

### Phase 1B: Opportunity Queue

Deliver:

- `content_opportunities`
- queue refresh and status flow
- project-page queue panel

### Phase 1C: Content Graph Layer

Deliver:

- `content_nodes`
- `content_edges`
- graph sync on approval
- graph page rendering for content assets

## Success Criteria

Phase 1 is successful when:

- a user can start a Blog/SEO content run from the project page
- the system produces a visible brief, plan, draft, and review result set
- the user can revise and approve the draft from the UI
- the project page shows prioritized content opportunities
- approved content appears in the content graph
- existing campaigns, graph, performance, monitoring, and chat flows remain functional

## Risks

### Artifact semantics drift

Mitigation:

- define content artifact types up front and keep them stable

### Reviewer noise

Mitigation:

- classify findings by severity and only auto-trigger revisions for meaningful findings

### Weak queue quality

Mitigation:

- every queue item must include explicit business rationale and recommended action

### Graph visual overload

Mitigation:

- render only approved or high-value content nodes in Phase 1

## Recommendation

Proceed with:

- Phase 1A first
- Phase 1B second
- Phase 1C third

This yields immediate user-visible value without requiring a full rewrite and preserves a clean path for later expansion into social-channel content workflows.
