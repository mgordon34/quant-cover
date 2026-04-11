import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from quant_cover_api.db.models.player import Player
from quant_cover_api.db.models.player_alias import PlayerAlias
from quant_cover_api.scraping.parsers.nba_api_boxscore import ParsedPlayerBoxscore

logger = logging.getLogger(__name__)


class PlayerResolutionService:
    def __init__(self, *, session: Session) -> None:
        self.session = session

    def resolve_or_create_player(self, *, league_id: int, parsed_player: ParsedPlayerBoxscore) -> Player:
        if parsed_player.source_player_id is not None:
            player = self.session.scalar(
                select(Player).where(
                    Player.league_id == league_id,
                    Player.source_player_id == parsed_player.source_player_id,
                )
            )
            if player is not None:
                self._update_player(player=player, parsed_player=parsed_player)
                return player

        normalized_alias = self._normalize_alias(parsed_player.display_name or parsed_player.full_name)
        if normalized_alias:
            player = self.session.scalar(
                select(Player)
                .join(PlayerAlias, PlayerAlias.player_id == Player.id)
                .where(
                    Player.league_id == league_id,
                    PlayerAlias.source == "nba_api",
                    PlayerAlias.normalized_alias == normalized_alias,
                )
            )
            if player is not None:
                self._ensure_player_source_id_matches(player=player, parsed_player=parsed_player)
                self._update_player(player=player, parsed_player=parsed_player)
                return player

        player = self.session.scalar(
            select(Player).where(
                Player.league_id == league_id,
                Player.full_name == parsed_player.full_name,
            )
        )
        if player is not None:
            self._ensure_player_source_id_matches(player=player, parsed_player=parsed_player)
            self._update_player(player=player, parsed_player=parsed_player)
            return player

        player = Player(
            league_id=league_id,
            full_name=parsed_player.full_name,
            display_name=parsed_player.display_name,
            source_player_id=parsed_player.source_player_id,
            primary_position=parsed_player.primary_position,
        )
        self.session.add(player)
        self.session.flush()
        logger.info(
            f"created player league_id={league_id} full_name={parsed_player.full_name} "
            f"source_player_id={parsed_player.source_player_id}"
        )
        return player

    def _update_player(self, *, player: Player, parsed_player: ParsedPlayerBoxscore) -> None:
        if player.source_player_id is None and parsed_player.source_player_id is not None:
            player.source_player_id = parsed_player.source_player_id
        if parsed_player.display_name and player.display_name != parsed_player.display_name:
            player.display_name = parsed_player.display_name
        if player.primary_position is None and parsed_player.primary_position is not None:
            player.primary_position = parsed_player.primary_position

    def _ensure_player_source_id_matches(self, *, player: Player, parsed_player: ParsedPlayerBoxscore) -> None:
        if parsed_player.source_player_id is None or player.source_player_id in (None, parsed_player.source_player_id):
            return
        raise ValueError(
            f"player source id mismatch for full_name={parsed_player.full_name}: "
            f"existing={player.source_player_id} incoming={parsed_player.source_player_id}"
        )

    def _normalize_alias(self, value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
        return re.sub(r"\s+", " ", normalized)
