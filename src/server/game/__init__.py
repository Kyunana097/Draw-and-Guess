"""
服务器游戏逻辑模块

实现房间、玩家、回合与计分等核心逻辑，供网络层调用以驱动游戏流程。

设计原则：
- 严谨的状态机：房间未开始/已开始；回合未激活/激活/结束
- 并发安全：网络线程并行调用，通过锁保护读写
- 信息分级：公开状态与画手私密信息分离
- 可扩展性：提供必要的钩子与接口（如定时更新）
"""

from __future__ import annotations

import random
import time
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from src.shared.constants import (
	MAX_PLAYERS,
	MIN_PLAYERS,
	ROUND_TIME,
	DRAW_TIME,
)


@dataclass
class PlayerState:
	"""玩家状态"""

	player_id: str
	name: str
	score: int = 0
	is_connected: bool = True


@dataclass
class RoundState:
	"""回合状态"""

	round_index: int = 0
	drawer_id: Optional[str] = None
	word: Optional[str] = None
	start_ts: Optional[float] = None
	guesses: Dict[str, str] = field(default_factory=dict)
	solved_by: Optional[str] = None
	is_active: bool = False

	def time_left(self) -> int:
		"""剩余作画/猜词时间（秒）"""
		# // 若回合未激活或未设置起始时间，则无剩余时间
		if not self.is_active or self.start_ts is None:
			return 0
		# // 使用 DRAW_TIME 作为本回合的计时长度
		deadline = self.start_ts + DRAW_TIME
		return max(0, int(deadline - time.time()))


@dataclass
class GameState:
	"""房间游戏状态"""

	players: Dict[str, PlayerState] = field(default_factory=dict)
	current_round: RoundState = field(default_factory=RoundState)
	is_started: bool = False
	rounds_played: int = 0


class GameRoom:
	"""游戏房间，管理玩家与回合"""

	def __init__(self, room_id: str, words_path: Optional[Path] = None):
		self.room_id = room_id
		self.state = GameState()
		self._words = self._load_words(words_path)
		self._drawer_cycle: List[str] = []
		# // 并发锁，保护状态修改（网络线程可能并发调用）
		self._lock = threading.RLock()

	# 玩家管理
	def add_player(self, player_id: str, name: str) -> bool:
		"""加入玩家，返回是否成功"""
		# // 保护并发状态
		with self._lock:
			if player_id in self.state.players:
				return False
			if len(self.state.players) >= MAX_PLAYERS:
				return False
			self.state.players[player_id] = PlayerState(player_id=player_id, name=name)
			self._rebuild_drawer_cycle()
			return True

	def remove_player(self, player_id: str) -> None:
		"""移除玩家，若画手离开则强制结束当前回合"""
		with self._lock:
			if player_id in self.state.players:
				del self.state.players[player_id]
				self._rebuild_drawer_cycle()
				# // 若画手离开，结束当前回合，避免阻塞游戏
				if self.state.current_round.drawer_id == player_id:
					self._force_end_round()

	def _rebuild_drawer_cycle(self) -> None:
		"""重建画手轮转队列，随机打乱以公平轮换"""
		self._drawer_cycle = list(self.state.players.keys())
		random.shuffle(self._drawer_cycle)

	# 游戏控制
	def start_game(self) -> bool:
		"""启动游戏，满足最小玩家数才可开始"""
		with self._lock:
			if self.state.is_started:
				return False
			if len(self.state.players) < MIN_PLAYERS:
				return False
			self.state.is_started = True
			self.state.rounds_played = 0
			return self.start_round()

	def start_round(self) -> bool:
		"""启动一个新回合：选画手，选词，设置计时"""
		with self._lock:
			if not self.state.is_started:
				return False
			if not self._drawer_cycle:
				self._rebuild_drawer_cycle()
			drawer_id = self._next_drawer()
			word = self._pick_word()
			self.state.current_round = RoundState(
				round_index=self.state.rounds_played + 1,
				drawer_id=drawer_id,
				word=word,
				start_ts=time.time(),
				is_active=True,
			)
			return True

	def _next_drawer(self) -> Optional[str]:
		"""轮转取画手（队首弹出再推回队尾）"""
		if not self._drawer_cycle:
			return None
		pid = self._drawer_cycle.pop(0)
		self._drawer_cycle.append(pid)
		return pid

	def submit_guess(self, player_id: str, guess_text: str) -> Tuple[bool, int]:
		"""提交猜词，返回 (是否正确, 获得分数)"""
		with self._lock:
			rnd = self.state.current_round
			# // 基本约束判定
			if not rnd.is_active:
				return False, 0
			if player_id == rnd.drawer_id:
				return False, 0
			if player_id not in self.state.players:
				return False, 0
			if rnd.solved_by:
				return False, 0

			# // 记录最后一次猜词（可扩展为历史）
			rnd.guesses[player_id] = guess_text

			# // 严格化文本比较（清理空白、标点、大小写）
			if self._normalize(guess_text) == self._normalize(rnd.word or ""):
				rnd.solved_by = player_id
				gained = self._score_for_first_solver(rnd)
				self.state.players[player_id].score += gained
				# // 画手奖励（按一半计分）
				if rnd.drawer_id and rnd.drawer_id in self.state.players:
					self.state.players[rnd.drawer_id].score += max(1, gained // 2)
				# // 回合结束
				self._finish_round()
				return True, gained
			return False, 0

	def next_round(self) -> bool:
		"""进入下一回合（要求游戏已开始）"""
		with self._lock:
			if not self.state.is_started:
				return False
			# // 累计已完成的回合数
			self.state.rounds_played += 1
			return self.start_round()

	def end_game(self) -> None:
		"""结束当前游戏（不重置玩家分数）"""
		with self._lock:
			self.state.is_started = False
			self._force_end_round()

	# 状态/视图
	def get_public_state(self) -> Dict[str, Any]:
		"""公开状态视图：不包含谜题答案，仅提供必要 UI 信息"""
		with self._lock:
			s = self.state
			r = s.current_round
			# // 公共玩家信息（name+score），便于客户端渲染记分板
			players_view = {
				pid: {"name": p.name, "score": p.score}
				for pid, p in s.players.items()
			}
			return {
				"room_id": self.room_id,
				"is_started": s.is_started,
				"round_index": r.round_index,
				"drawer_id": r.drawer_id,
				"time_left": r.time_left(),
				"players": players_view,
				"solved": bool(r.solved_by),
			}

	def get_private_state_for(self, player_id: str) -> Dict[str, Any]:
		"""私密状态视图：仅画手可见谜题答案"""
		with self._lock:
			r = self.state.current_round
			# // 非画手不暴露答案
			secret_word = r.word if player_id == r.drawer_id else None
			return {
				"round_index": r.round_index,
				"is_active": r.is_active,
				"drawer_id": r.drawer_id,
				"word": secret_word,
				"time_left": r.time_left(),
			}

	def reset_room(self) -> None:
		"""重置房间状态（清空回合与分数）"""
		with self._lock:
			self.state = GameState()
			self._rebuild_drawer_cycle()

	# 定时/辅助
	def update_timeouts(self) -> bool:
		"""超时检查：若回合时间到则结束回合，返回是否发生状态变化"""
		with self._lock:
			r = self.state.current_round
			if r.is_active and r.time_left() <= 0:
				# // 超时未解，直接结束回合（无额外计分）
				self._finish_round()
				return True
			return False

	# 内部方法
	def _finish_round(self) -> None:
		"""标记回合结束"""
		# // 不重置已猜中标记，以便客户端渲染“已解”状态
		self.state.current_round.is_active = False

	def _force_end_round(self) -> None:
		"""强制结束当前回合（如画手离线等）"""
		self.state.current_round.is_active = False
		self.state.current_round.solved_by = None

	@staticmethod
	def _normalize(text: str) -> str:
		"""文本标准化：去空白与常见标点，统一小写"""
		# // 去除 Unicode 空白与标点（中英文）
		t = (text or "").lower()
		t = re.sub(r"[\s\p{Punct}]+", "", t)
		# // Python 的 re 不原生支持 \p{Punct}，补充常见标点集合
		t = re.sub(r"[\s,.;:!?'\-_/\\\(\)\[\]{}，。；：！？（ ）【 】]", "", t)
		return t

	@staticmethod
	def _load_words(words_path: Optional[Path]) -> List[str]:
		"""加载词库，若失败使用默认应急词"""
		base = words_path or Path(__file__).parents[3] / "data" / "words.txt"
		items: List[str] = []
		try:
			with open(base, "r", encoding="utf-8") as f:
				for line in f:
					t = line.strip()
					if not t or t.startswith("#"):
						continue
					items.append(t)
		except (FileNotFoundError, OSError, UnicodeDecodeError):
			items = ["苹果", "猫", "房子", "太阳"]
		return items

	def _pick_word(self) -> Optional[str]:
		"""从词库中随机抽选一个词"""
		if not self._words:
			return None
		return random.choice(self._words)

	def _score_for_first_solver(self, rnd: RoundState) -> int:
		"""首个猜中计分：随剩余时间递减，确保公平"""
		# // 设最大 10 分、最小 3 分，根据剩余比例线性分配
		left = max(0, rnd.time_left())
		total = max(1, DRAW_TIME)
		ratio = left / total
		score = int(round(3 + 7 * ratio))
		return max(3, min(10, score))


__all__ = [
	"PlayerState",
	"RoundState",
	"GameState",
	"GameRoom",
]

