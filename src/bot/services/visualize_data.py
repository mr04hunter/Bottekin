import io
import re
from typing import TYPE_CHECKING
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


if TYPE_CHECKING:
    from bot.types.leaderboards.database_layer import ServerActivityData


class GraphService:
    def create_graph(self, data: "ServerActivityData") -> io.BytesIO:
        days = np.arange(len(data.labels))

        BG     = "#1A1919FF"
        GREEN  = "#0FDA52"
        PURPLE = "#531DB6"
        ORANGE = "#DF633A"
        MUTED  = "#888888"

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.yaxis.grid(True, color="#363636", linewidth=0.8)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        ax.plot(days, data.feedback_data, color=GREEN, lw=2.5, marker="o", ms=5,
                markerfacecolor=GREEN, markeredgecolor=BG, markeredgewidth=1.5,
                label="feedback")
        ax.fill_between(days, data.feedback_data, alpha=0.10, color=GREEN)

        ax.plot(days, data.track_data, color=ORANGE, lw=2.5, marker="s", ms=5,
                markerfacecolor=ORANGE, markeredgecolor=BG, markeredgewidth=1.5,
                label="track")
        ax.fill_between(days, data.track_data, alpha=0.10, color=ORANGE)

        ax.plot(days, data.total, color=PURPLE, lw=2.5, marker="^", ms=5,
                markerfacecolor=PURPLE, markeredgecolor=BG, markeredgewidth=1.5,
                linestyle="--", label="total")
        ax.fill_between(days, data.total, alpha=0.10, color=PURPLE)

        ax.set_xlabel("Date", fontsize=12, color=MUTED, labelpad=10)
        ax.set_ylabel("Posts", fontsize=12, color=MUTED, labelpad=10)
        ax.tick_params(colors=MUTED, labelsize=11, length=0)
        ax.set_xticks(days)                                        
        ax.set_xticklabels([f"{d}" for d in data.labels])           

        legend_elements = [
            Line2D([0],[0], color=GREEN,  lw=2.5, marker="o", ms=5,
                markerfacecolor=GREEN,  markeredgecolor=BG, label="feedback"),
            Line2D([0],[0], color=ORANGE, lw=2.5, marker="s", ms=5,
                markerfacecolor=ORANGE, markeredgecolor=BG, label="track"),
            Line2D([0],[0], color=PURPLE, lw=2.5, marker="^", ms=5,
                markerfacecolor=PURPLE, markeredgecolor=BG,
                linestyle="--", label="total"),
        ]

        ax.legend(
            handles=legend_elements,
            bbox_to_anchor=(1, 1),
            bbox_transform=fig.transFigure,
            frameon=False,
            fontsize=11,
            labelcolor=MUTED
        )

        ax.set_title("Server Activity in Community Feedback Category",
                    fontsize=14, fontweight="medium", color="#e0e0e0",
                    pad=16, loc="left")

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)
        return buf