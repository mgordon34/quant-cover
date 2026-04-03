# NBA Data Schema Spec

## Goal

Define the first sports-data schema for Quant Cover.

This schema is:

- NBA-first
- extensible to other leagues later
- designed for scraping from Stathead-owned properties and similar sources
- designed to support later odds-source mapping
- normalized enough for backtesting and analytics without overbuilding

This document is the implementation spec for the next database expansion after the current `users`, `strategies`, and `backtest_runs` tables.

## Design Decisions

### Canonical entities vs source-specific identifiers

Core entities should stay canonical:

- `sports`
- `leagues`
- `teams`
- `players`
- `games`
- `player_game_stats`

Source-specific identifiers should not be represented with generic column names like `index`.

For the first pass, Stathead-specific identifiers can live on the canonical tables as explicit `stathead_*_id` columns.

If a second or third source becomes important, add a separate `external_ids` table instead of overloading the canonical tables further.

### Naming

- use `player_game_stats`, not `player_games`
- use explicit `stathead_*_id` names, not `index`
- use `game_date` for the calendar date
- also include `started_at` when tipoff time matters
- use `metadata` only as an escape hatch, not for core fields

### Scope

This spec includes:

- canonical sports data tables
- alias support for player name matching
- recommended constraints and indexes
- a phased migration plan

This spec does not yet include:

- odds tables
- sportsbook market tables
- roster history tables
- ingestion run tracking tables
- strategy-facing derived feature tables

## Table Spec

### `sports`

Purpose:
- top-level sport metadata

Columns:
- `id` `bigint` primary key
- `key` `varchar(64)` not null unique
- `name` `varchar(255)` not null
- `stathead_domain` `varchar(255)` nullable
- `created_at` `timestamptz` not null
- `updated_at` `timestamptz` not null

Example rows:
- `basketball`
- `baseball`

Constraints:
- unique `key`

Notes:
- do not use `nba` here; `nba` belongs in `leagues`

### `leagues`

Purpose:
- competition within a sport

Columns:
- `id` `bigint` primary key
- `sport_id` `bigint` not null references `sports(id)` on delete cascade
- `key` `varchar(64)` not null unique
- `name` `varchar(255)` not null
- `stathead_league_key` `varchar(64)` nullable
- `odds_api_sport_key` `varchar(128)` nullable
- `is_active` `boolean` not null default `true`
- `created_at` `timestamptz` not null
- `updated_at` `timestamptz` not null

Example rows:
- `nba`
- `wnba`
- `mlb`

Indexes:
- index on `sport_id`

Constraints:
- unique `key`

### `teams`

Purpose:
- canonical team records

Columns:
- `id` `bigint` primary key
- `league_id` `bigint` not null references `leagues(id)` on delete cascade
- `name` `varchar(255)` not null
- `abbreviation` `varchar(32)` not null
- `is_active` `boolean` not null default `true`
- `created_at` `timestamptz` not null
- `updated_at` `timestamptz` not null

Indexes:
- index on `league_id`

Constraints:
- unique `(league_id, abbreviation)`

Notes:
- `abbreviation` is expected to match the Stathead team code in the first implementation
- if that assumption stops holding once more sources are added, introduce a dedicated external identifier table later

### `players`

Purpose:
- canonical player records

Columns:
- `id` `bigint` primary key
- `league_id` `bigint` not null references `leagues(id)` on delete cascade
- `full_name` `varchar(255)` not null
- `display_name` `varchar(255)` not null
- `stathead_player_id` `varchar(64)` nullable
- `primary_position` `varchar(32)` nullable
- `birth_date` `date` nullable
- `metadata` `jsonb` nullable
- `created_at` `timestamptz` not null
- `updated_at` `timestamptz` not null

Indexes:
- index on `(league_id, full_name)`

Constraints:
- unique `(league_id, stathead_player_id)`

Notes:
- `display_name` is the preferred product/UI name
- `full_name` is the canonical stored full name
- `metadata` should stay sparse and only hold fields not yet promoted into first-class columns

### `player_aliases`

Purpose:
- alternate player names per source for fuzzy and deterministic matching

Columns:
- `id` `bigint` primary key
- `player_id` `bigint` not null references `players(id)` on delete cascade
- `stathead_source` `varchar(64)` not null
- `alias` `varchar(255)` not null
- `normalized_alias` `varchar(255)` not null
- `created_at` `timestamptz` not null
- `updated_at` `timestamptz` not null

Indexes:
- index on `player_id`
- index on `normalized_alias`

Constraints:
- unique `(stathead_source, normalized_alias)`

Notes:
- `normalized_alias` should be a deterministic normalized form used for matching
- recommended normalization includes lowercase, whitespace collapse, punctuation cleanup, and suffix handling decisions

### `games`

Purpose:
- canonical game records for scheduled and completed games

Columns:
- `id` `bigint` primary key
- `league_id` `bigint` not null references `leagues(id)` on delete cascade
- `season` `varchar(32)` nullable
- `season_type` `varchar(32)` nullable
- `game_date` `date` not null
- `started_at` `timestamptz` nullable
- `status` `varchar(32)` not null
- `home_team_id` `bigint` not null references `teams(id)` on delete restrict
- `away_team_id` `bigint` not null references `teams(id)` on delete restrict
- `home_score` `integer` nullable
- `away_score` `integer` nullable
- `stathead_game_id` `varchar(64)` nullable
- `created_at` `timestamptz` not null
- `updated_at` `timestamptz` not null

Suggested `status` values for the first pass:
- `scheduled`
- `in_progress`
- `completed`
- `postponed`
- `cancelled`

Indexes:
- index on `(league_id, game_date)`
- index on `home_team_id`
- index on `away_team_id`

Constraints:
- unique `(league_id, stathead_game_id)`
- check `home_team_id <> away_team_id`
- check `status in ('scheduled', 'in_progress', 'completed', 'postponed', 'cancelled')`

Notes:
- keep `game_date` even if `started_at` is present; date-only filtering is common
- `season_type` can remain a string initially; move to a stricter enum later if needed

### `player_game_stats`

Purpose:
- one player stat line for one game

Columns:
- `id` `bigint` primary key
- `player_id` `bigint` not null references `players(id)` on delete cascade
- `game_id` `bigint` not null references `games(id)` on delete cascade
- `team_id` `bigint` not null references `teams(id)` on delete restrict
- `opponent_team_id` `bigint` not null references `teams(id)` on delete restrict
- `started` `boolean` nullable
- `minutes` `numeric(5,2)` nullable
- `points` `integer` nullable
- `rebounds` `integer` nullable
- `assists` `integer` nullable
- `threes_made` `integer` nullable
- `steals` `integer` nullable
- `blocks` `integer` nullable
- `turnovers` `integer` nullable
- `offensive_rating` `numeric(6,2)` nullable
- `defensive_rating` `numeric(6,2)` nullable
- `stathead_row_id` `varchar(64)` nullable
- `metadata` `jsonb` nullable
- `created_at` `timestamptz` not null
- `updated_at` `timestamptz` not null

Indexes:
- unique `(player_id, game_id)`
- index on `game_id`
- index on `team_id`
- index on `opponent_team_id`

Notes:
- `team_id` and `opponent_team_id` are intentionally duplicated here to simplify downstream analytics
- `minutes` should be numeric rather than integer because minute values often include partial minutes

## Explicitly Deferred Tables

These should not be part of the first migration unless implementation pressure appears:

- `external_ids`
- `team_aliases`
- `roster_memberships`
- `ingestion_runs`
- `odds_markets`
- `odds_prices`
- `player_prop_lines`

## Migration Plan

### Migration 1: sports and leagues

Add:
- `sports`
- `leagues`

Seed immediately after migration:
- `sports.key = basketball`
- `leagues.key = nba`

### Migration 2: teams and players

Add:
- `teams`
- `players`
- `player_aliases`

Why separate from games:
- ingestion of teams and players is the cleanest first source-sync step

### Migration 3: games and player game stats

Add:
- `games`
- `player_game_stats`

Why separate from players:
- lets ingestion start with low-risk dimensions before fact tables

## Recommended SQLAlchemy Model Names

- `Sport`
- `League`
- `Team`
- `Player`
- `PlayerAlias`
- `Game`
- `PlayerGameStat`

## Recommended Relationships

- `Sport.leagues`
- `League.sport`
- `League.teams`
- `League.players`
- `League.games`
- `Team.league`
- `Team.home_games`
- `Team.away_games`
- `Team.player_game_stats`
- `Player.league`
- `Player.aliases`
- `Player.player_game_stats`
- `Game.league`
- `Game.home_team`
- `Game.away_team`
- `Game.player_game_stats`
- `PlayerAlias.player`
- `PlayerGameStat.player`
- `PlayerGameStat.game`
- `PlayerGameStat.team`
- `PlayerGameStat.opponent_team`

## Ingestion Implications

### First source: Stathead / Sports Reference

Expected mapping:
- teams -> `abbreviation`
- players -> `stathead_player_id`
- games -> `stathead_game_id`

Expected first sync order:
1. sync teams
2. sync players
3. sync games
4. sync player game stats

### Name matching

For players, matching should use this order:
1. exact Stathead id match
2. exact alias match on `(stathead_source, normalized_alias)`
3. exact canonical name match within league
4. unresolved record handling later

Do not implement fuzzy matching in the first pass.

## Open Decisions For Review

### 1. Global players vs league-specific players

Current spec choice:
- players are league-scoped using `league_id`

Reason:
- simpler now
- matches current NBA-first scope
- avoids premature complexity around multi-league player identity

If you expect cross-league identity soon, this should be revisited before migration.

### 2. `stathead_*_id` vs `external_ids`

Current spec choice:
- explicit `stathead_player_id` and `stathead_game_id`
- use `teams.abbreviation` as the Stathead team code in the first implementation

Reason:
- simpler for the first implementation
- works well with a single primary source

If you expect multiple active sources early, use an `external_ids` table instead.

### 3. `season_type`

Current spec choice:
- free text string with expected known values

Reason:
- lower migration friction

This spec now includes a status check constraint for `games.status`.

## Suggested Follow-Up Implementation Sequence

1. review and approve this spec
2. implement SQLAlchemy models for `Sport`, `League`, `Team`, `Player`, `PlayerAlias`, `Game`, `PlayerGameStat`
3. create Alembic migrations in the same phase grouping defined above
4. add seed support for `sports` and `leagues`
5. add CLI ingestion scaffold for NBA teams and players
6. add first Stathead / Sports Reference client and parser

## Questions To Resolve Before Implementation

1. Do you want `started` in `player_game_stats` in the first migration, or would you prefer to keep only the box-score stat columns initially?
2. Do you want `teams.abbreviation` to remain the canonical team code permanently, or should we reserve a more generic `code` column name before implementation?
3. Do you want `player_aliases.stathead_source` to stay explicit, or should it be generalized only when a second source actually appears?
