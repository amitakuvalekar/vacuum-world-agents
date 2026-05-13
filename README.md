# Vacuum World Agents

A visual, interactive comparison of three classic AI agent architectures applied to the **3-room vacuum world** problem.

## Problem

Three rooms (A, B, C) are each either **Clean** or **Dirty**. An agent starts at a random room and must clean all dirty rooms using three actions: `Clean`, `Left`, `Right`.

## Agents

| Agent | Strategy | Memory |
|---|---|---|
| **Simple Reflex** | If dirty → Clean; else bounce off walls | None |
| **Model-Based** | Tracks internal map of room states; navigates to nearest known-dirty room | Room states + visited flags |
| **Goal-Based** | Runs BFS over the full state space before acting; executes the optimal plan | Full BFS search tree |

## Features

- Step-by-step animation of all three agents running simultaneously
- Random starting state (rooms and agent position) on every run
- Per-agent **Start** buttons and a **Start All** button
- **Run 50 Iterations** button — computes 50 random trials, refreshes stats, plays rapid animation, and pops up a **move-count distribution chart**
- Live stats panel: Min / Avg / Max moves and solve rate across trials

## Requirements

```
Python 3.8+
matplotlib
```

Install dependencies:

```bash
pip install matplotlib
```

## Usage

```bash
python vacuum_world.py
```

## How It Works

### Simple Reflex Agent

**Technology: A hardcoded if/else rule table**

```python
if status == DIRTY:
    return "Clean"
if pos == 0:
    return "Right"
if pos == 2:
    return "Left"
```

Just a lookup — current percept in, action out. No state, no planning.

---

### Model-Based Agent

**Technology: A manually maintained state array**

```python
self.model[pos] = status      # update internal map from percept
self.visited[pos] = True
# then navigate toward nearest known-dirty room
```

Two plain Python lists (`model[]` and `visited[]`) act as the agent's memory. Decision is a `min()` call to find the nearest dirty room.

---

### Goal-Based Agent

**Technology: Breadth-First Search (BFS)**

```python
queue = deque([(start, [])])
# expand states until all rooms are CLEAN
```

Uses Python's built-in `collections.deque` to do BFS over the state space `(agent_position, rooms_tuple)`. Finds the shortest possible action sequence before taking a single step. No heuristics — pure uninformed search.

---

### Visualisation

**Technology: Matplotlib**

- `matplotlib.patches` — draws the room rectangles and agent circles
- `matplotlib.widgets.Button` — the interactive buttons
- `fig.canvas.new_timer()` — drives the frame-by-frame animation

---

### Summary

| Agent | Core technique | Python tool |
|---|---|---|
| Simple Reflex | Condition-action rules | `if/else` |
| Model-Based | Internal state tracking | Plain lists |
| Goal-Based | Optimal path search | `collections.deque` (BFS) |
| UI | Animation & widgets | `matplotlib` |

## Results (averaged over 200 random starting states)

| Agent | Avg Moves | Always Solves? |
|---|---|---|
| Simple Reflex | ~3.0 | Yes |
| Model-Based | ~3.1 | Yes |
| Goal-Based | ~2.9 | Yes |

All three solve every starting state in the 3-room world. The Goal-Based agent edges out the lowest average because BFS guarantees the globally shortest path.

## High-Level Implementation

### 1. Environment (`Env` class)

A simple object holding an array of 3 room states (`CLEAN`/`DIRTY`) and the agent's current position. It has one method — `act(action)` — that mutates state based on the action taken. Nothing intelligent lives here; it's just the world.

---

### 2. The Three Agents

Each agent has a `run(states, pos)` method that returns the full history of states and list of actions taken.

| Agent | Decision logic |
|---|---|
| **Simple Reflex** | Looks only at the current room. If dirty → clean. If clean → bounce off walls (reverse at A or C, otherwise continue direction). No memory. |
| **Model-Based** | Keeps an internal `model[]` array. Updates it each step from what it currently sees. Navigates toward the nearest room its model believes is dirty; if none, explores unvisited rooms. |
| **Goal-Based** | Runs BFS over the full state space `(position, rooms_tuple)` before moving a single step, finds the shortest action sequence to reach all-clean, then executes it blindly. |

---

### 3. The Animated UI

```
plt.figure
├── 3 agent_axes          ← one panel per agent (redrawn each frame)
├── stats_ax              ← static table + bar chart
└── 5 Button widgets      ← Start Reflex / Start Model / Start Goal
                             Start All / Run 50 Iterations
```

Two timers drive everything:
- **Normal timer (850 ms)** — advances the frame counter for whichever agents have `play=True`, redraws their panel
- **Batch timer (100 ms)** — when "Run 50" is clicked, cycles through all 50 pre-computed trials rapidly, drawing one frame per tick

All mutable state lives in a single `st` dict (histories, current frames, play flags) and a `batch` dict (trial list, current trial/frame index). The buttons just flip flags in these dicts — the timers do the actual rendering.

---

### 4. "Run 50 Iterations" Flow

```
Button click
  → compute all 50 trials instantly (pure Python loop, no drawing)
  → recalculate stats → redraw stats panel
  → dump trials into batch dict
  → set batch["running"] = True
  → batch timer fires every 100ms, stepping through each trial's frames
  → when all 50 done, restore normal title
```

