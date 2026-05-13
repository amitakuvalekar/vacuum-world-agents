#!/usr/bin/env python3
"""
3-Room Vacuum World — Agent Comparison with Visual Animation
============================================================
Rooms : A  B  C   (each Clean or Dirty)
Actions: Clean | Left | Right
Agents :
  1. Simple Reflex   — reacts to current percept only, no memory
  2. Model-Based     — keeps an internal map of all rooms
  3. Goal-Based      — computes optimal plan via BFS before acting
"""

import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.widgets import Button
from collections import deque

# ─── Colour palette ──────────────────────────────────────────────────
BG     = "#0D1117"
PANEL  = "#161B22"
GREEN  = "#3FB950"
RED    = "#F85149"
ORANGE = "#D29922"
WHITE  = "#E6EDF3"
GREY   = "#8B949E"
BORDER = "#30363D"

CLEAN, DIRTY = 0, 1
MAX_STEPS    = 50
NUM_TRIALS   = 50


# ════════════════════════════════════════════════════════════════════════
#  ENVIRONMENT
# ════════════════════════════════════════════════════════════════════════

class Env:
    """Simulates the 3-room vacuum world."""

    def __init__(self, states, pos):
        self.rooms = list(states)
        self.pos   = int(pos)
        self.steps = 0

    def is_done(self):
        return all(r == CLEAN for r in self.rooms)

    def percept(self):
        """Return (position, dirt-status-of-current-room)."""
        return self.pos, self.rooms[self.pos]

    def snap(self):
        """Immutable snapshot: (position, rooms-tuple)."""
        return self.pos, tuple(self.rooms)

    def act(self, action):
        self.steps += 1
        if action == "Clean":
            self.rooms[self.pos] = CLEAN
        elif action == "Left" and self.pos > 0:
            self.pos -= 1
        elif action == "Right" and self.pos < 2:
            self.pos += 1


# ════════════════════════════════════════════════════════════════════════
#  SIMPLE REFLEX AGENT
#  Percept → Action via fixed rules. Zero memory of other rooms.
#  Rule: if dirty → clean; else bounce between walls.
# ════════════════════════════════════════════════════════════════════════

class SimpleReflexAgent:
    name  = "Simple Reflex Agent"
    color = RED

    def __init__(self):
        self._dir = 1           # current travel direction (+1=right, -1=left)

    def reset(self):
        self._dir = 1

    def choose(self, percept):
        pos, status = percept
        if status == DIRTY:
            return "Clean"
        if pos == 0:
            self._dir = 1
            return "Right"
        if pos == 2:
            self._dir = -1
            return "Left"
        return "Right" if self._dir == 1 else "Left"

    def run(self, states, pos):
        env = Env(states, pos)
        self.reset()
        H, A = [env.snap()], ["—"]
        while not env.is_done() and env.steps < MAX_STEPS:
            a = self.choose(env.percept())
            env.act(a)
            H.append(env.snap())
            A.append(a)
        return H, A, env.steps, env.is_done()


# ════════════════════════════════════════════════════════════════════════
#  MODEL-BASED AGENT
#  Maintains an internal map of room states; updates it from each percept.
#  Navigation: go to nearest known-dirty room; explore unvisited if none.
# ════════════════════════════════════════════════════════════════════════

class ModelBasedAgent:
    name  = "Model-Based Agent"
    color = "#BC8CFF"

    def reset(self):
        self.model   = [DIRTY] * 3     # assume dirty until seen otherwise
        self.visited = [False] * 3

    def choose(self, percept):
        pos, status = percept
        # Update internal model from current percept
        self.model[pos]   = status
        self.visited[pos] = True

        if status == DIRTY:
            return "Clean"

        # Prioritise known-dirty rooms; fall back to unvisited
        dirty     = [i for i in range(3) if self.model[i] == DIRTY]
        unvisited = [i for i in range(3) if not self.visited[i]]
        targets   = dirty if dirty else unvisited

        if not targets:
            return "Clean"   # model says all done (shouldn't reach here)

        t = min(targets, key=lambda i: abs(i - pos))
        if t < pos:   return "Left"
        elif t > pos: return "Right"
        else:         return "Clean"

    def run(self, states, pos):
        env = Env(states, pos)
        self.reset()
        H, A = [env.snap()], ["—"]
        while not env.is_done() and env.steps < MAX_STEPS:
            a = self.choose(env.percept())
            env.act(a)
            H.append(env.snap())
            A.append(a)
        return H, A, env.steps, env.is_done()


# ════════════════════════════════════════════════════════════════════════
#  GOAL-BASED AGENT
#  BFS over state-space to find the minimum-step plan before acting.
#  State = (agent_pos, rooms_tuple); goal = all rooms CLEAN.
# ════════════════════════════════════════════════════════════════════════

class GoalBasedAgent:
    name  = "Goal-Based Agent"
    color = GREEN

    def plan(self, states, pos):
        """Return optimal action list via BFS."""
        start = (pos, tuple(states))
        if all(s == CLEAN for s in states):
            return []

        queue   = deque([(start, [])])
        visited = {start}

        while queue:
            (p, rooms), path = queue.popleft()

            for action in ["Clean", "Left", "Right"]:
                np_, nr = p, list(rooms)

                if action == "Clean":
                    nr[p] = CLEAN
                elif action == "Left":
                    if p == 0:
                        continue
                    np_ -= 1
                elif action == "Right":
                    if p == 2:
                        continue
                    np_ += 1

                new_state = (np_, tuple(nr))
                new_path  = path + [action]

                if all(r == CLEAN for r in new_state[1]):
                    return new_path

                if new_state not in visited:
                    visited.add(new_state)
                    queue.append((new_state, new_path))

        return []   # unreachable for valid inputs

    def run(self, states, pos):
        env  = Env(states, pos)
        plan = self.plan(states, pos)
        H, A = [env.snap()], ["—"]
        for a in plan:
            env.act(a)
            H.append(env.snap())
            A.append(a)
        return H, A, env.steps, env.is_done()


# ════════════════════════════════════════════════════════════════════════
#  STATISTICS
# ════════════════════════════════════════════════════════════════════════

def compute_stats(agents):
    total_moves  = [0] * len(agents)
    total_solved = [0] * len(agents)
    all_counts   = [[] for _ in agents]

    for _ in range(NUM_TRIALS):
        states = [random.choice([CLEAN, DIRTY]) for _ in range(3)]
        if all(s == CLEAN for s in states):
            states[random.randint(0, 2)] = DIRTY
        pos = random.randint(0, 2)

        for k, ag in enumerate(agents):
            _, _, mv, done = ag.run(list(states), pos)
            total_moves[k]  += mv
            all_counts[k].append(mv)
            if done:
                total_solved[k] += 1

    avgs = [t / NUM_TRIALS for t in total_moves]
    mins = [min(c) for c in all_counts]
    maxs = [max(c) for c in all_counts]
    return avgs, mins, maxs, total_solved


# ════════════════════════════════════════════════════════════════════════
#  DRAWING HELPERS
# ════════════════════════════════════════════════════════════════════════

# Axis space: x ∈ [0, 4.4],  y ∈ [0, 4.0]
ROOM_CX = [0.80, 2.20, 3.60]   # x-centres of the three rooms
ROOM_Y  = 1.35                  # y of room bottom edge
ROOM_W  = 1.10
ROOM_H  = 1.10


def draw_agent_panel(ax, snap, action, step, done, color, name, total_steps):
    ax.clear()
    ax.set_xlim(0.0, 4.4)
    ax.set_ylim(0.0, 4.0)
    ax.set_facecolor(PANEL)
    ax.axis("off")

    # Coloured border frame
    border = mpatches.FancyBboxPatch(
        (0.03, 0.03), 4.34, 3.94,
        boxstyle="round,pad=0.0",
        facecolor="none", edgecolor=color,
        linewidth=2.5, zorder=10
    )
    ax.add_patch(border)

    pos, rooms = snap

    # ── Agent name header ───────────────────────────────────────
    ax.text(2.20, 3.82, name,
            ha="center", va="top", color=color,
            fontsize=9.5, fontweight="bold", fontfamily="monospace")

    # ── Room rectangles ─────────────────────────────────────────
    for i, (rx, status) in enumerate(zip(ROOM_CX, rooms)):
        fc = GREEN if status == CLEAN else RED

        rect = mpatches.FancyBboxPatch(
            (rx - ROOM_W / 2, ROOM_Y), ROOM_W, ROOM_H,
            boxstyle="round,pad=0.07",
            facecolor=fc, edgecolor=WHITE,
            linewidth=1.8, alpha=0.88, zorder=2
        )
        ax.add_patch(rect)

        # Room letter above box
        ax.text(rx, ROOM_Y + ROOM_H + 0.20, f"Room {chr(65 + i)}",
                ha="center", va="bottom",
                color=WHITE, fontsize=10, fontweight="bold")

        # Dirt status inside box
        label = "CLEAN" if status == CLEAN else "DIRTY"
        icon  = "✓" if status == CLEAN else "✗"
        ax.text(rx, ROOM_Y + ROOM_H * 0.55, icon,
                ha="center", va="center",
                color=WHITE, fontsize=18, fontweight="bold", zorder=3)
        ax.text(rx, ROOM_Y + ROOM_H * 0.22, label,
                ha="center", va="center",
                color=WHITE, fontsize=7.5, fontweight="bold", zorder=3)

    # ── Agent robot marker ──────────────────────────────────────
    rx = ROOM_CX[pos]
    ay = ROOM_Y - 0.55

    # Shadow
    shadow = mpatches.Ellipse((rx, ay - 0.08), 0.52, 0.14,
                               facecolor="black", alpha=0.30, zorder=3)
    ax.add_patch(shadow)

    # Body circle
    body = mpatches.Circle((rx, ay), 0.27,
                            facecolor=color, edgecolor=WHITE,
                            linewidth=2.0, zorder=5)
    ax.add_patch(body)

    # "R" label inside circle
    ax.text(rx, ay, "R", ha="center", va="center",
            color=WHITE, fontsize=9, fontweight="bold", zorder=6)

    # Dashed connector to room
    ax.plot([rx, rx], [ay + 0.27, ROOM_Y],
            color=color, lw=1.5, ls="--", alpha=0.50, zorder=4)

    # ── Action badge ────────────────────────────────────────────
    act_col = ORANGE if action not in ("—",) else GREY

    action_icons = {"Clean": "[CLEAN]", "Left": "<< Left",
                    "Right": "Right >>", "—": "-- Start"}
    act_display = action_icons.get(action, action)

    ax.text(2.20, 0.70, act_display,
            ha="center", va="center",
            color=act_col, fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35",
                      facecolor=BG, edgecolor=act_col,
                      linewidth=1.5, alpha=0.92), zorder=7)

    # ── Step counter / done banner ──────────────────────────────
    if done and step > 0:
        status_txt = f"Step {step}  ✓  DONE!"
        sc         = GREEN
    else:
        status_txt = f"Step {step} / {total_steps}"
        sc         = GREY

    ax.text(2.20, 0.24, status_txt,
            ha="center", va="center", color=sc, fontsize=8.5)


def draw_stats_panel(ax, agents, avgs, mins, maxs, solved):
    ax.clear()
    ax.set_facecolor(PANEL)
    ax.axis("off")

    ax.text(0.50, 0.96,
            f"Performance over {NUM_TRIALS} random starting states",
            transform=ax.transAxes, ha="center", va="top",
            color=WHITE, fontsize=9.5, fontweight="bold")

    # Separator
    from matplotlib.lines import Line2D
    line = Line2D([0.02, 0.98], [0.76, 0.76],
                  transform=ax.transAxes, color=BORDER, linewidth=1)
    ax.add_line(line)

    # ── Table: left 55% ─────────────────────────────────────────
    headers = ["Agent", "Min", "Avg", "Max", f"Solved/{NUM_TRIALS}"]
    col_x   = [0.11, 0.26, 0.36, 0.46, 0.54]

    for hx, h in zip(col_x, headers):
        ax.text(hx, 0.74, h, transform=ax.transAxes,
                ha="center", va="top", color=GREY,
                fontsize=8.5, fontweight="bold")

    for k, ag in enumerate(agents):
        y = 0.52 - k * 0.23
        row = [ag.name, str(mins[k]), f"{avgs[k]:.1f}", str(maxs[k]), f"{solved[k]}"]
        for col, v in zip(col_x, row):
            c  = ag.color if col == col_x[0] else WHITE
            fw = "bold"   if col == col_x[0] else "normal"
            ax.text(col, y, v, transform=ax.transAxes,
                    ha="center", va="center", color=c,
                    fontsize=8.5, fontweight=fw)

    # Vertical divider between table and bar chart
    from matplotlib.lines import Line2D as _L2D
    ax.add_line(_L2D([0.62, 0.62], [0.05, 0.95],
                     transform=ax.transAxes, color=BORDER, linewidth=1))

    # ── Bar chart: right 38% ────────────────────────────────────
    ax.text(0.80, 0.90, "Avg Moves Comparison",
            transform=ax.transAxes, ha="center", va="top",
            color=GREY, fontsize=8, fontweight="bold")

    colors = [ag.color for ag in agents]
    bar_labels = ["Reflex", "Model", "Goal"]
    xs = [0.69, 0.80, 0.91]
    bar_w = 0.07
    bar_y0, bar_h_scale = 0.10, 0.62
    max_avg = max(avgs) if max(avgs) > 0 else 1

    for x, avg, col, lbl in zip(xs, avgs, colors, bar_labels):
        bh = (avg / max_avg) * bar_h_scale
        rect = mpatches.FancyBboxPatch(
            (x - bar_w / 2, bar_y0), bar_w, bh,
            boxstyle="round,pad=0.01",
            transform=ax.transAxes,
            facecolor=col, edgecolor=WHITE,
            linewidth=1.0, alpha=0.88,
            zorder=5, clip_on=False
        )
        ax.add_patch(rect)
        ax.text(x, bar_y0 + bh + 0.04, f"{avg:.1f}",
                transform=ax.transAxes,
                ha="center", va="bottom", color=col,
                fontsize=8, fontweight="bold")
        ax.text(x, bar_y0 - 0.04, lbl,
                transform=ax.transAxes,
                ha="center", va="top", color=GREY, fontsize=7.5)


# ════════════════════════════════════════════════════════════════════════
#  DISTRIBUTION PLOT  (opened by "Run 50 Iterations")
# ════════════════════════════════════════════════════════════════════════

def plot_distribution(agents, move_counts, solved, NUM):
    """
    Open a new figure showing, per agent:
      • bar chart of move-count frequencies
      • mean line, min/max annotations
      • termination rate
    """
    from collections import Counter

    dist_fig, axes = plt.subplots(1, 3, figsize=(14, 5.5), facecolor=BG)
    dist_fig.suptitle(
        f"Move Count Distribution  —  {NUM} Random Trials",
        color=WHITE, fontsize=13, fontweight="bold"
    )

    for ax, ag, counts, sol in zip(axes, agents, move_counts, solved):
        ax.set_facecolor(PANEL)
        for spine in ax.spines.values():
            spine.set_color(ag.color)
            spine.set_linewidth(1.8)

        freq     = Counter(counts)
        mn, mx   = min(counts), max(counts)
        avg      = sum(counts) / NUM
        term_pct = sol / NUM * 100
        x_vals   = list(range(mn, mx + 1))
        y_vals   = [freq.get(x, 0) for x in x_vals]

        # Bars
        bars = ax.bar(x_vals, y_vals,
                      color=ag.color, edgecolor=WHITE,
                      linewidth=0.9, alpha=0.85, width=0.55, zorder=3)

        # Frequency label on each bar
        for bar, y in zip(bars, y_vals):
            if y > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.15,
                        str(y), ha="center", va="bottom",
                        color=WHITE, fontsize=8.5, fontweight="bold")

        # Mean vertical line
        ax.axvline(avg, color=ORANGE, linewidth=2, linestyle="--",
                   alpha=0.9, zorder=4, label=f"Mean: {avg:.2f}")

        # Stats annotation box (top-right)
        box_txt = (
            f"Mean : {avg:.2f}\n"
            f"Min  : {mn}\n"
            f"Max  : {mx}\n"
            f"Solved: {sol}/{NUM}  ({term_pct:.0f}%)"
        )
        ax.text(0.97, 0.97, box_txt,
                transform=ax.transAxes, ha="right", va="top",
                color=WHITE, fontsize=8.5, fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.45",
                          facecolor=BG, edgecolor=ag.color,
                          linewidth=1.2, alpha=0.92))

        ax.set_title(ag.name, color=ag.color,
                     fontsize=11, fontweight="bold", pad=10)
        ax.set_xlabel("Moves to Clean All Rooms", color=GREY, fontsize=9)
        ax.set_ylabel("Number of Trials",         color=GREY, fontsize=9)
        ax.set_xticks(x_vals)
        ax.tick_params(colors=GREY, labelsize=9)
        ax.set_xlim(mn - 0.6, mx + 0.6)
        ax.set_ylim(0, max(y_vals) * 1.22)
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.legend(loc="upper left", fontsize=8.5,
                  facecolor=BG, edgecolor=BORDER, labelcolor=ORANGE)
        ax.grid(axis="y", color=BORDER, linewidth=0.6, alpha=0.5, zorder=0)

    dist_fig.tight_layout(pad=2.5)
    dist_fig.canvas.draw()
    dist_fig.canvas.manager.show()


# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════

def make_random_start():
    states = [random.choice([CLEAN, DIRTY]) for _ in range(3)]
    if all(s == CLEAN for s in states):
        states[random.randint(0, 2)] = DIRTY
    return states, random.randint(0, 2)


def main():
    random.seed(None)   # fresh randomness on every run

    agents = [SimpleReflexAgent(), ModelBasedAgent(), GoalBasedAgent()]

    # ── Pre-compute stats ─────────────────────────────────────────
    print("=" * 60)
    print("  3-ROOM VACUUM WORLD — AGENT COMPARISON")
    print("=" * 60)
    print(f"  Running {NUM_TRIALS} random trials for statistics ...")
    avgs, mins, maxs, solved = compute_stats(agents)
    print(f"\n  {'Agent':<24} {'Min':>5} {'Avg':>6} {'Max':>5} {'Solved':>8}")
    print("  " + "-" * 52)
    for ag, mn, av, mx, sol in zip(agents, mins, avgs, maxs, solved):
        print(f"  {ag.name:<24} {mn:>5} {av:>6.1f} {mx:>5}   {sol}/{NUM_TRIALS}")
    print("=" * 60)
    print("  Window open — click a Start button to begin.")

    # ════════════════════════════════════════════════════════════
    #  Figure layout  (all axes placed manually so Button widgets
    #  can sit between agent panels and the stats panel)
    #
    #   y=0.95-1.00  title
    #   y=0.46-0.94  3 agent panels
    #   y=0.40-0.45  per-agent Start buttons   (3 buttons)
    #   y=0.34-0.39  "Start All" button        (centred)
    #   y=0.03-0.32  stats panel
    # ════════════════════════════════════════════════════════════
    fig = plt.figure(figsize=(15, 9.5), facecolor=BG)

    # Agent panel axes
    panel_xs = [0.025, 0.345, 0.665]
    panel_w, panel_h = 0.295, 0.48
    agent_axes = [fig.add_axes([x, 0.46, panel_w, panel_h])
                  for x in panel_xs]

    # Stats panel
    stats_ax = fig.add_axes([0.025, 0.03, 0.95, 0.29])
    draw_stats_panel(stats_ax, agents, avgs, mins, maxs, solved)

    # ── Shared mutable state ─────────────────────────────────────
    st = {
        "states": [DIRTY, DIRTY, DIRTY],
        "pos":    1,
        "hist":   [None, None, None],   # history per agent
        "acts":   [None, None, None],   # actions per agent
        "frame":  [0,    0,    0   ],
        "total":  [0,    0,    0   ],
        "done":   [False,False,False],
        "play":   [False,False,False],
    }

    # ── Drawing helpers ──────────────────────────────────────────
    def _draw(i):
        f       = min(st["frame"][i], len(st["hist"][i]) - 1)
        is_done = (f == len(st["hist"][i]) - 1) and st["done"][i]
        draw_agent_panel(
            agent_axes[i], st["hist"][i][f], st["acts"][i][f],
            f, is_done, agents[i].color, agents[i].name, st["total"][i]
        )

    def _update_title():
        s, p = st["states"], st["pos"]
        fig.suptitle(
            "3-Room Vacuum World  |  Simple Reflex  vs  Model-Based  vs  Goal-Based\n"
            f"Random start — A={'D' if s[0]==DIRTY else 'C'}  "
            f"B={'D' if s[1]==DIRTY else 'C'}  "
            f"C={'D' if s[2]==DIRTY else 'C'}  "
            f"|  Agent begins at Room {chr(65+p)}",
            color=WHITE, fontsize=11, fontweight="bold", y=0.995, va="top"
        )

    def load_random_state():
        """Pick a new random state, compute each agent's plan, show frame 0."""
        states, pos       = make_random_start()
        st["states"], st["pos"] = states, pos
        for i, ag in enumerate(agents):
            H, A, mv, done      = ag.run(list(states), pos)
            st["hist"][i]       = H
            st["acts"][i]       = A
            st["frame"][i]      = 0
            st["total"][i]      = mv
            st["done"][i]       = done
            st["play"][i]       = False
            _draw(i)
        _update_title()
        # Print new state to console
        s, p = st["states"], st["pos"]
        print(f"\n  [New state]  A={'D' if s[0]==DIRTY else 'C'} "
              f"B={'D' if s[1]==DIRTY else 'C'} "
              f"C={'D' if s[2]==DIRTY else 'C'}  "
              f"| Start Room {chr(65+p)}")
        for i, ag in enumerate(agents):
            plan = " -> ".join(st["acts"][i][1:]) or "(none)"
            print(f"    {ag.name:<22} {st['total'][i]:>2} moves  {plan}")

    # ── Batch state (used by the Run-200 feature) ────────────────
    batch = {
        "trials":  None,   # list of (states,pos,Hs,As,mvs,dones)
        "idx":     0,      # which trial we are showing
        "frame":   0,      # which frame inside that trial
        "running": False,
    }

    # ── Normal step timer (850 ms — per-agent playback) ──────────
    def on_timer():
        if batch["running"]:
            return
        changed = False
        for i in range(3):
            if st["play"][i] and st["hist"][i] is not None:
                st["frame"][i] += 1
                if st["frame"][i] >= len(st["hist"][i]):
                    st["frame"][i] = len(st["hist"][i]) - 1
                    st["play"][i]  = False
                _draw(i)
                changed = True
        if changed:
            fig.canvas.draw_idle()

    timer = fig.canvas.new_timer(interval=850)
    timer.add_callback(on_timer)
    timer.start()

    # ── Batch timer (100 ms — rapid 200-iteration playback) ──────
    def on_batch_timer():
        if not batch["running"]:
            return

        trials = batch["trials"]
        idx    = batch["idx"]

        # All 200 trials done
        if idx >= len(trials):
            batch["running"] = False
            _update_title()
            for i in range(3):
                _draw(i)
            fig.canvas.draw_idle()
            print(f"  [Batch complete]  200 / 200 trials finished.")
            return

        states, pos, Hs, As, mvs, dones = trials[idx]
        frame     = batch["frame"]
        max_frame = max(len(H) for H in Hs)

        if frame >= max_frame:
            # Advance to next trial
            batch["idx"]   += 1
            batch["frame"]  = 0
            trial_num = batch["idx"]
            fig.suptitle(
                f"Running 50 Iterations — Trial {trial_num} / 50  "
                f"({'complete' if trial_num == 50 else 'in progress...'})",
                color=ORANGE, fontsize=11, fontweight="bold",
                y=0.995, va="top"
            )
            fig.canvas.draw_idle()
            return

        # Draw current frame across all 3 agents
        for i in range(3):
            f = min(frame, len(Hs[i]) - 1)
            st["hist"][i]  = Hs[i]
            st["acts"][i]  = As[i]
            st["frame"][i] = f
            st["total"][i] = mvs[i]
            st["done"][i]  = dones[i]
            _draw(i)

        batch["frame"] += 1
        fig.canvas.draw_idle()

    batch_timer = fig.canvas.new_timer(interval=100)
    batch_timer.add_callback(on_batch_timer)
    batch_timer.start()

    # ── Helper: abort any running batch ──────────────────────────
    def stop_batch():
        if batch["running"]:
            batch["running"] = False
            batch["trials"]  = None

    # ── Per-agent Start buttons ───────────────────────────────────
    per_btns = []
    for i, x in enumerate(panel_xs):
        bax = fig.add_axes([x + 0.01, 0.405, 0.275, 0.045])
        lbl = f"> Start  {agents[i].name.replace(' Agent', '')}"
        btn = Button(bax, lbl, color="#21262D", hovercolor="#2D333B")
        btn.label.set_color(agents[i].color)
        btn.label.set_fontsize(9.5)
        btn.label.set_fontweight("bold")
        per_btns.append(btn)

    def make_start_one(idx):
        def cb(event):
            stop_batch()
            load_random_state()
            st["play"][idx] = True
        return cb

    for i, btn in enumerate(per_btns):
        btn.on_clicked(make_start_one(i))

    # ── "Start All" button ────────────────────────────────────────
    all_ax  = fig.add_axes([0.18, 0.345, 0.27, 0.045])
    all_btn = Button(all_ax, ">> Start All Agents",
                     color="#21262D", hovercolor="#2D333B")
    all_btn.label.set_color(ORANGE)
    all_btn.label.set_fontsize(9.5)
    all_btn.label.set_fontweight("bold")

    def on_start_all(event):
        stop_batch()
        load_random_state()
        for i in range(3):
            st["play"][i] = True
        fig.canvas.draw_idle()

    all_btn.on_clicked(on_start_all)

    # ── "Run 200 Iterations" button ───────────────────────────────
    r200_ax  = fig.add_axes([0.55, 0.345, 0.28, 0.045])
    r200_btn = Button(r200_ax, ">> Run 50 Iterations",
                      color="#21262D", hovercolor="#2D333B")
    r200_btn.label.set_color("#58A6FF")   # blue
    r200_btn.label.set_fontsize(9.5)
    r200_btn.label.set_fontweight("bold")

    def on_run_200(event):
        stop_batch()
        for i in range(3):
            st["play"][i] = False

        # Show computing banner
        fig.suptitle("Computing 50 iterations ...",
                     color=ORANGE, fontsize=11, fontweight="bold",
                     y=0.995, va="top")
        fig.canvas.draw_idle()
        fig.canvas.flush_events()

        # Run all 200 trials and collect full histories
        NUM = 50
        trials = []
        move_counts = [[] for _ in range(3)]

        for t in range(NUM):
            states, pos = make_random_start()
            Hs, As, mvs, dones = [], [], [], []
            for ag in agents:
                H, A, mv, done = ag.run(list(states), pos)
                Hs.append(H); As.append(A)
                mvs.append(mv); dones.append(done)
                move_counts[agents.index(ag)].append(mv)
            trials.append((states, pos, Hs, As, mvs, dones))

        # Refresh stats panel with the fresh 200-trial data
        new_avgs   = [sum(c) / NUM         for c in move_counts]
        new_mins   = [min(c)               for c in move_counts]
        new_maxs   = [max(c)               for c in move_counts]
        new_solved = [sum(1 for r in trials if r[5][i]) for i in range(3)]
        draw_stats_panel(stats_ax, agents, new_avgs, new_mins, new_maxs, new_solved)

        # Print summary to console
        print(f"\n  [Run 50 complete]")
        print(f"  {'Agent':<24} {'Min':>5} {'Avg':>6} {'Max':>5} {'Solved':>8}")
        print("  " + "-" * 52)
        for ag, mn, av, mx, sol in zip(agents, new_mins, new_avgs, new_maxs, new_solved):
            print(f"  {ag.name:<24} {mn:>5} {av:>6.1f} {mx:>5}   {sol}/{NUM}")

        # Open distribution plot in a new window
        plot_distribution(agents, move_counts, new_solved, NUM)

        # Kick off the rapid playback through all 50 trials
        batch["trials"]  = trials
        batch["idx"]     = 0
        batch["frame"]   = 0
        batch["running"] = True
        fig.canvas.draw_idle()

    r200_btn.on_clicked(on_run_200)

    # ── Initial display ───────────────────────────────────────────
    load_random_state()
    fig.canvas.draw_idle()

    plt.show()


if __name__ == "__main__":
    main()
