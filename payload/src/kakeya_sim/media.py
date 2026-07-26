from __future__ import annotations

from pathlib import Path
import math
import shutil

import matplotlib
matplotlib.use("Agg")


def _configure_runtime() -> None:
    """Configure CJK fonts and an FFmpeg executable for every environment."""
    preferred_fonts = [
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "Noto Sans SC",
        "Microsoft YaHei",
        "SimHei",
        "DejaVu Sans",
    ]
    matplotlib.rcParams["font.sans-serif"] = preferred_fonts
    matplotlib.rcParams["axes.unicode_minus"] = False

    if shutil.which("ffmpeg"):
        return

    try:
        import imageio_ffmpeg
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise RuntimeError(
            "FFmpeg is unavailable. Install the ffmpeg system package or imageio-ffmpeg."
        ) from exc

    executable = imageio_ffmpeg.get_ffmpeg_exe()
    if not executable or not Path(executable).is_file():
        raise RuntimeError("imageio-ffmpeg did not provide a valid FFmpeg executable.")
    matplotlib.rcParams["animation.ffmpeg_path"] = executable


_configure_runtime()

import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
import numpy as np

from .geometry import Tube
from .voxel import VoxelResult


def _sample_union_points(voxel: VoxelResult, seed: int, maximum: int = 2500) -> tuple[np.ndarray, np.ndarray]:
    occupied = np.flatnonzero(voxel.multiplicity > 0)
    if occupied.size == 0:
        return np.empty((0, 3)), np.empty((0,))
    rng = np.random.default_rng(seed)
    if occupied.size > maximum:
        occupied = rng.choice(occupied, size=maximum, replace=False)
    return voxel.points[occupied], voxel.multiplicity[occupied]


def _draw_scene(ax: plt.Axes, tubes: list[Tube], voxel: VoxelResult, seed: int) -> None:
    points, multiplicity = _sample_union_points(voxel, seed)
    if points.size:
        ax.scatter(
            points[:, 0], points[:, 1], points[:, 2],
            c=multiplicity, cmap="viridis", s=4,
            alpha=0.22, linewidths=0,
        )

    groups = max(1, max(t.group for t in tubes) + 1)
    cmap = plt.get_cmap("tab20")
    for tube in tubes:
        color = cmap((tube.group % groups) / groups)
        ax.plot(
            [tube.a[0], tube.b[0]],
            [tube.a[1], tube.b[1]],
            [tube.a[2], tube.b[2]],
            linewidth=max(1.0, 55.0 * tube.radius),
            alpha=0.62, color=color, solid_capstyle="round",
        )

    u = np.linspace(0, 2 * math.pi, 28)
    v = np.linspace(0, math.pi, 14)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_wireframe(x, y, z, rstride=3, cstride=3, linewidth=0.25, alpha=0.10)

    ax.set_xlim(-1.08, 1.08)
    ax.set_ylim(-1.08, 1.08)
    ax.set_zlim(-1.08, 1.08)
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.grid(False)
    ax.set_title("R³ 中 Kakeya δ-管并集")


def create_preview(tubes: list[Tube], voxel: VoxelResult, output: Path, seed: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(10, 8), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    _draw_scene(ax, tubes, voxel, seed)
    ax.view_init(elev=23, azim=38)
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def create_rotation_video(
    tubes: list[Tube],
    voxel: VoxelResult,
    mp4_output: Path,
    gif_output: Path,
    seed: int,
    frames: int = 60,
    fps: int = 15,
) -> None:
    mp4_output.parent.mkdir(parents=True, exist_ok=True)
    gif_output.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(8, 8), dpi=110)
    ax = fig.add_subplot(111, projection="3d")
    _draw_scene(ax, tubes, voxel, seed)

    def update(frame: int):
        angle = 360.0 * frame / max(1, frames)
        elevation = 21.0 + 7.0 * math.sin(2.0 * math.pi * frame / max(1, frames))
        ax.view_init(elev=elevation, azim=angle)
        return ()

    animation = FuncAnimation(fig, update, frames=frames, interval=1000 / max(1, fps), blit=False)
    animation.save(mp4_output, writer=FFMpegWriter(fps=fps, bitrate=2200))
    animation.save(gif_output, writer=PillowWriter(fps=max(5, min(fps, 12))))
    plt.close(fig)
