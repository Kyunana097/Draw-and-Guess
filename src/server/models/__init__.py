"""
数据模型模块

定义游戏中的数据结构，如玩家、房间、回合、聊天与计分等。
该模块提供严格类型的 dataclass、序列化与规范化工具，便于网络层与游戏层协同。
"""

from __future__ import annotations

import time
import enum
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from src.shared.constants import (
	MAX_PLAYERS,
	MIN_PLAYERS,
	ROUND_TIME,
	DRAW_TIME,
)


class RoundPhase(enum.Enum):
	"""回合阶段枚举"""

	WAITING = "waiting"  # // 等待开始（尚未激活）
	DRAWING = "drawing"  # // 作画+猜词进行中（激活）
	ENDED = "ended"      # // 回合已结束（解答或超时）


@dataclass
class RoomConfig:
	"""房间配置模型（与常量保持一致，可覆盖）"""

	max_players: int = MAX_PLAYERS
	min_players: int = MIN_PLAYERS
	round_time: int = ROUND_TIME
	draw_time: int = DRAW_TIME

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)

	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> "RoomConfig":
		return cls(
			max_players=int(data.get("max_players", MAX_PLAYERS)),
			min_players=int(data.get("min_players", MIN_PLAYERS)),
			round_time=int(data.get("round_time", ROUND_TIME)),
			draw_time=int(data.get("draw_time", DRAW_TIME)),
		)


@dataclass
class Player:
	"""玩家模型"""

	player_id: str
	name: str
	score: int = 0
	joined_ts: float = field(default_factory=lambda: time.time())
	last_seen_ts: float = field(default_factory=lambda: time.time())
	is_connected: bool = True

	def touch(self) -> None:
		# // 更新最后活跃时间（心跳/消息收发）
		self.last_seen_ts = time.time()

	def to_public(self) -> Dict[str, Any]:
		# // 公开视图：仅暴露必要字段供 UI 使用
		return {
			"player_id": self.player_id,
			"name": self.name,
			"score": self.score,
			"is_connected": self.is_connected,
		}

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)

	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> "Player":
		return cls(
			player_id=str(data["player_id"]),
			name=str(data["name"]),
			score=int(data.get("score", 0)),
			joined_ts=float(data.get("joined_ts", time.time())),
			last_seen_ts=float(data.get("last_seen_ts", time.time())),
			is_connected=bool(data.get("is_connected", True)),
		)


@dataclass
class GuessRecord:
	"""猜词记录（便于审计与玩法扩展）"""

	player_id: str
	text: str
	ts: float = field(default_factory=lambda: time.time())
	is_correct: bool = False

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)


@dataclass
class ChatRecord:
	"""聊天记录模型"""

	player_id: str
	text: str
	ts: float = field(default_factory=lambda: time.time())

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)


@dataclass
class ScoreEvent:
	"""计分事件（记录分数变化的原因与时间）"""

	player_id: str
	delta: int
	reason: str
	ts: float = field(default_factory=lambda: time.time())

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)


@dataclass
class DrawingAction:
	"""绘图动作（同步画笔数据）"""

	# // 为便于传输，尽量保持数据简洁
	player_id: str
	kind: str  # // begin|point|end 等
	color: Tuple[int, int, int]
	size: int
	point: Optional[Tuple[int, int]] = None
	ts: float = field(default_factory=lambda: time.time())

	def to_dict(self) -> Dict[str, Any]:
		return {
			"player_id": self.player_id,
			"kind": self.kind,
			"color": list(self.color),
			"size": self.size,
			"point": list(self.point) if self.point else None,
			"ts": self.ts,
		}

	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> "DrawingAction":
		pt = data.get("point")
		return cls(
			player_id=str(data["player_id"]),
			kind=str(data["kind"]),
			color=tuple(map(int, data["color"])),
			size=int(data["size"]),
			point=tuple(map(int, pt)) if pt else None,
			ts=float(data.get("ts", time.time())),
		)


@dataclass
class Round:
	"""回合模型（与游戏层 RoundState 语义一致，作为纯模型层）"""

	index: int = 0
	drawer_id: Optional[str] = None
	word: Optional[str] = None
	phase: RoundPhase = RoundPhase.WAITING
	start_ts: Optional[float] = None
	end_ts: Optional[float] = None
	guesses: List[GuessRecord] = field(default_factory=list)
	solved_by: Optional[str] = None

	def activate(self) -> None:
		# // 开始作画/猜词阶段
		self.phase = RoundPhase.DRAWING
		self.start_ts = time.time()
		self.end_ts = None

	def finish(self) -> None:
		# // 结束当前回合（超时或猜中）
		self.phase = RoundPhase.ENDED
		self.end_ts = time.time()

	def time_left(self, draw_time: int = DRAW_TIME) -> int:
		# // 返回剩余秒数；未激活则为 0
		if self.phase != RoundPhase.DRAWING or not self.start_ts:
			return 0
		deadline = self.start_ts + max(1, draw_time)
		return max(0, int(deadline - time.time()))

	def is_active(self) -> bool:
		return self.phase == RoundPhase.DRAWING

	def mask_word_for_public(self) -> Optional[str]:
		# // 对公开视图隐藏谜底：以同长度掩码字符显示
		if not self.word:
			return None
		return "●" * len(self.word)

	def add_guess(self, player_id: str, text: str) -> GuessRecord:
		# // 添加一条猜词记录；是否正确由外部判定后写回
		rec = GuessRecord(player_id=player_id, text=text)
		self.guesses.append(rec)
		return rec

	def to_public(self) -> Dict[str, Any]:
		# // 公开视图：不包含答案，仅基础信息
		return {
			"index": self.index,
			"drawer_id": self.drawer_id,
			"phase": self.phase.value,
			"time_left": self.time_left(),
			"solved": bool(self.solved_by),
			"word_mask": self.mask_word_for_public(),
		}

	def to_private_for(self, player_id: str) -> Dict[str, Any]:
		# // 私密视图：仅画手可见答案
		return {
			"index": self.index,
			"drawer_id": self.drawer_id,
			"phase": self.phase.value,
			"time_left": self.time_left(),
			"word": self.word if player_id == self.drawer_id else None,
		}

	def to_dict(self) -> Dict[str, Any]:
		return {
			"index": self.index,
			"drawer_id": self.drawer_id,
			"word": self.word,
			"phase": self.phase.value,
			"start_ts": self.start_ts,
			"end_ts": self.end_ts,
			"guesses": [g.to_dict() for g in self.guesses],
			"solved_by": self.solved_by,
		}

	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> "Round":
		rd = cls(
			index=int(data.get("index", 0)),
			drawer_id=data.get("drawer_id"),
			word=data.get("word"),
			phase=RoundPhase(str(data.get("phase", RoundPhase.WAITING.value))),
			start_ts=data.get("start_ts"),
			end_ts=data.get("end_ts"),
			solved_by=data.get("solved_by"),
		)
		rd.guesses = [GuessRecord(**g) for g in data.get("guesses", [])]
		return rd


# 工具函数
def normalize_text(text: str) -> str:
	"""文本标准化：去空白与常见标点，统一为小写，匹配游戏判定"""
	t = (text or "").lower()
	# // 移除空白
	t = re.sub(r"\s+", "", t)
	# // 移除常见标点（中英文）
	t = re.sub(r"[,.;:!?'\-_/\\\(\)\[\]{}，。；：！？（ ）【 】]", "", t)
	return t


__all__ = [
	"RoundPhase",
	"RoomConfig",
	"Player",
	"GuessRecord",
	"ChatRecord",
	"ScoreEvent",
	"DrawingAction",
	"Round",
	"normalize_text",
]

