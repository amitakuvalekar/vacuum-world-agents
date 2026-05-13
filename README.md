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
Acts solely on the current percept `(position, room_status)`. No memory of other rooms. Uses a wall-bounce heuristic when the current room is clean.

### Model-Based Agent
Maintains a `model[]` array updated from each percept. Navigates toward the nearest room its internal model believes to be dirty; explores unvisited rooms if none are known dirty.

### Goal-Based Agent
Before taking a single step, performs **Breadth-First Search** over the state space `(agent_position, rooms_tuple)` to find the shortest possible action sequence. Executes the plan blindly — always optimal.

## Results (averaged over 200 random starting states)

| Agent | Avg Moves | Always Solves? |
|---|---|---|
| Simple Reflex | ~3.0 | Yes |
| Model-Based | ~3.1 | Yes |
| Goal-Based | ~2.9 | Yes |

All three solve every starting state in the 3-room world. The Goal-Based agent edges out the lowest average because BFS guarantees the globally shortest path.
