"""蛇梯棋（Snakes and Ladders）引擎。

规则：
- 10x10 棋盘，共 100 格（1..100），蛇形编号：1 在左下角。
- 每轮掷 6 面骰，走对应步数。
- 踩到梯子底部 -> 爬到顶部；踩到蛇头 -> 滑到蛇尾。
- 必须精确到达 100 才获胜：掷出的步数超出则原地不动（也可以理解为"反弹"规则的简化版，这里采用"原地不动"）。
- "AI" 只是幌子：纯运气游戏，--auto 只是自动掷骰演示，顺带输出统计。

纯标准库：argparse / random / sys / copy。
"""

import argparse
import copy
import random
import sys

BOARD_SIZE = 100

# 梯子：起点（底）-> 终点（顶）
LADDERS = {
    2: 38,
    4: 14,
    9: 31,
    21: 42,
    28: 84,
    36: 44,
    51: 67,
    71: 91,
    80: 100,
}

# 蛇：蛇头 -> 蛇尾
SNAKES = {
    16: 6,
    47: 26,
    49: 11,
    56: 53,
    62: 19,
    64: 60,
    87: 24,
    93: 73,
    95: 75,
    98: 78,
}


class SnakesLadders:
    """可测试的游戏核心：状态是每位玩家的位置列表（起点 0 = 棋盘外）。"""

    def __init__(self, n_players=2, ladders=None, snakes=None, rng=None):
        if n_players < 2:
            raise ValueError("至少需要 2 名玩家")
        self.n_players = n_players
        self.ladders = dict(LADDERS if ladders is None else ladders)
        self.snakes = dict(SNAKES if snakes is None else snakes)
        # 校验：蛇/梯子的起点不能重叠
        if set(self.ladders) & set(self.snakes):
            raise ValueError("蛇头与梯底重叠")
        for s, e in list(self.ladders.items()) + list(self.snakes.items()):
            if not (1 <= s <= BOARD_SIZE and 1 <= e <= BOARD_SIZE):
                raise ValueError(f"蛇/梯子坐标越界: {s}->{e}")
        for s, e in self.ladders.items():
            if e <= s:
                raise ValueError(f"梯子必须向上: {s}->{e}")
        for s, e in self.snakes.items():
            if e >= s:
                raise ValueError(f"蛇必须向下: {s}->{e}")
        self.positions = [0] * n_players
        self.turn = 0
        self.winner = None
        self.moves = 0
        self.rng = rng if rng is not None else random.Random()

    # ---- 规则 ----

    def roll(self):
        return self.rng.randint(1, 6)

    def apply_roll(self, player, roll):
        """玩家 player 掷出 roll，返回 (新位置, 事件描述)。"""
        if player != self.turn:
            raise ValueError("走子顺序错误")
        if not 1 <= roll <= 6:
            raise ValueError("骰子点数必须 1..6")
        pos = self.positions[player]
        event = "普通移动"
        if pos + roll > BOARD_SIZE:
            new_pos = pos  # 超出：原地不动（需精确到达 100）
            event = f"掷出 {roll} 超出 100，原地不动"
        else:
            new_pos = pos + roll
            if new_pos in self.ladders:
                event = f"踩到梯子 {new_pos}，爬到 {self.ladders[new_pos]}"
                new_pos = self.ladders[new_pos]
            elif new_pos in self.snakes:
                event = f"踩到蛇头 {new_pos}，滑到 {self.snakes[new_pos]}"
                new_pos = self.snakes[new_pos]
        self.positions[player] = new_pos
        self.moves += 1
        if new_pos == BOARD_SIZE:
            self.winner = player
        else:
            self.turn = (self.turn + 1) % self.n_players
        return new_pos, event

    def is_over(self):
        return self.winner is not None

    def snapshot(self):
        return copy.deepcopy(self)

    # ---- 演示 ----

    def auto_game(self, verbose=False):
        """自动掷骰打完一局，返回 (winner, moves)。"""
        while not self.is_over():
            roll = self.roll()
            pos, event = self.apply_roll(self.turn, roll)
            if verbose:
                print(f"玩家{self.turn + 1} 掷 {roll} -> {pos}（{event}）")
            if self.moves > 100000:
                raise RuntimeError("对局异常：超过 10 万步未结束")
        return self.winner, self.moves

    # ---- 渲染 ----

    def render(self):
        """文本棋盘：蛇形编号，标注玩家位置（A/B/C/D...）。"""
        marks = {}
        for i, p in enumerate(self.positions):
            if p >= 1:
                marks.setdefault(p, []).append(chr(ord("A") + i))
        lines = []
        for row in range(9, -1, -1):
            cells = []
            for col in range(10):
                # 蛇形编号
                n = row * 10 + (col + 1 if row % 2 == 0 else 10 - col)
                tag = "".join(marks.get(n, []))
                if n in self.ladders:
                    tag += "▲"
                elif n in self.snakes:
                    tag += "▼"
                cells.append(f"{n:>3}{tag:<3}")
            lines.append(" ".join(cells))
        return "\n".join(lines)


def play_interactive(n_players=2, seed=None):
    rng = random.Random(seed)
    game = SnakesLadders(n_players=n_players, rng=rng)
    print("=== 蛇梯棋 ===")
    print("每位玩家轮流掷骰（按回车掷骰，q 退出），精确到达 100 获胜。")
    print("▲=梯底 ▼=蛇头\n")
    while not game.is_over():
        print(game.render())
        p = game.turn
        cmd = input(f"玩家{chr(ord('A') + p)} 回车掷骰 (q退出): ").strip()
        if cmd.lower() == "q":
            print("已退出。")
            return
        roll = game.roll()
        pos, event = game.apply_roll(p, roll)
        print(f"掷出 {roll}，走到 {pos}：{event}\n")
    print(game.render())
    print(f"玩家{chr(ord('A') + game.winner)} 获胜！共 {game.moves} 手。")


def play_auto(games=10, seed=None, n_players=2, verbose=False):
    rng = random.Random(seed)
    wins = [0] * n_players
    total_moves = 0
    min_moves = None
    max_moves = None
    for i in range(games):
        game = SnakesLadders(n_players=n_players, rng=rng)
        winner, moves = game.auto_game(verbose=verbose)
        wins[winner] += 1
        total_moves += moves
        min_moves = moves if min_moves is None else min(min_moves, moves)
        max_moves = moves if max_moves is None else max(max_moves, moves)
        if verbose:
            print(f"--- 第 {i + 1} 局：玩家{chr(ord('A') + winner)} 胜，用 {moves} 手 ---")
    print(f"共 {games} 局：")
    for i, w in enumerate(wins):
        print(f"  玩家{chr(ord('A') + i)} 胜 {w} 局")
    print(f"平均手数 {total_moves / games:.1f}，最短 {min_moves}，最长 {max_moves}")
    print("（蛇梯棋纯看运气，AI 对局只是自动掷骰演示。）")


def main(argv=None):
    ap = argparse.ArgumentParser(description="蛇梯棋 (Snakes and Ladders)")
    ap.add_argument("--players", type=int, default=2, help="玩家数（默认 2）")
    ap.add_argument("--auto", action="store_true", help="自动掷骰演示")
    ap.add_argument("--games", type=int, default=10, help="自动演示局数")
    ap.add_argument("--seed", type=int, default=None, help="随机种子")
    ap.add_argument("--verbose", action="store_true", help="自动演示打印每步")
    args = ap.parse_args(argv)
    if args.auto:
        play_auto(games=args.games, seed=args.seed, n_players=args.players,
                  verbose=args.verbose)
    else:
        if not sys.stdin.isatty():
            print("交互模式需要终端；无头演示请用 --auto。", file=sys.stderr)
            sys.exit(2)
        play_interactive(n_players=args.players, seed=args.seed)


if __name__ == "__main__":
    main()
