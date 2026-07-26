from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import plotly.graph_objects as go

from .geometry import Tube, orthonormal_frame
from .voxel import VoxelResult


def cylinder_mesh(tube: Tube, sides: int = 10) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[int], list[int], list[int]]:
    u, v, _ = orthonormal_frame(tube.direction)
    vertices: list[np.ndarray] = []
    for endpoint in (tube.a, tube.b):
        for k in range(sides):
            angle = 2.0 * math.pi * k / sides
            vertices.append(endpoint + tube.radius * (math.cos(angle) * u + math.sin(angle) * v))
    vertices.extend([tube.a, tube.b])
    a_center, b_center = 2 * sides, 2 * sides + 1
    ii: list[int] = []
    jj: list[int] = []
    kk: list[int] = []
    for k in range(sides):
        nxt = (k + 1) % sides
        ii.extend([k, k, a_center, sides + k, b_center, sides + k])
        jj.extend([nxt, sides + k, k, sides + nxt, sides + nxt, nxt])
        kk.extend([sides + k, nxt, nxt, nxt, sides + k, k])
    arr = np.asarray(vertices)
    return arr[:, 0], arr[:, 1], arr[:, 2], ii, jj, kk


def create_viewer(tubes: list[Tube], voxel: VoxelResult, output: Path, seed: int) -> None:
    fig = go.Figure()
    palette = [
        "#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c",
        "#0891b2", "#be123c", "#4f46e5", "#65a30d", "#a16207",
    ]
    for idx, tube in enumerate(tubes):
        x, y, z, i, j, k = cylinder_mesh(tube)
        fig.add_trace(
            go.Mesh3d(
                x=x, y=y, z=z, i=i, j=j, k=k,
                color=palette[tube.group % len(palette)],
                opacity=0.22,
                flatshading=True,
                name=f"管 {idx} / 分组 {tube.group}",
                hovertemplate=(
                    f"管={idx}<br>分组={tube.group}<br>"
                    f"center=({tube.center[0]:.3f},{tube.center[1]:.3f},{tube.center[2]:.3f})"
                    "<extra></extra>"
                ),
                showscale=False,
            )
        )

    occupied = np.flatnonzero(voxel.multiplicity > 0)
    rng = np.random.default_rng(seed)
    if occupied.size > 12_000:
        occupied = rng.choice(occupied, size=12_000, replace=False)
    points = voxel.points[occupied]
    mult = voxel.multiplicity[occupied]
    fig.add_trace(
        go.Scatter3d(
            x=points[:, 0], y=points[:, 1], z=points[:, 2],
            mode="markers",
            marker=dict(size=2.2, color=mult, colorscale="Turbo", opacity=0.6, colorbar=dict(title="重数")),
            name="体素化并集",
            hovertemplate="x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>重数=%{marker.color}<extra></extra>",
        )
    )
    fig.update_layout(
        title="三维 Kakeya δ-管数值模拟",
        scene=dict(
            xaxis_title="x", yaxis_title="y", zaxis_title="z",
            aspectmode="cube",
            xaxis=dict(range=[-1.05, 1.05]),
            yaxis=dict(range=[-1.05, 1.05]),
            zaxis=dict(range=[-1.05, 1.05]),
        ),
        template="plotly_white",
        margin=dict(l=0, r=0, b=0, t=45),
        legend=dict(itemsizing="constant"),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output, include_plotlyjs="inline", full_html=True)
