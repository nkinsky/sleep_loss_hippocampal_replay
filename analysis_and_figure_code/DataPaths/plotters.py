import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statannotations
from statannotations.Annotator import Annotator
from statannotations.stats.StatTest import StatTest
from subjects import colors_sd, stat_kw
from typing import Unpack, TypedDict, Union
from dataclasses import dataclass
import pandas as pd
import itertools
from subjects import adjust_lightness
from copy import deepcopy
import pingouin as pg
from neuropy.utils.misc import flatten

class Plotter:
    def __init__(
        self, data, x, y, hue=None, hue_order=None, xtick_rot=30, ax=None
    ) -> None:
        """Initiates data format for plotting

        Parameters
        ----------
        data : _type_
            _description_
        x : _type_
            _description_
        y : _type_
            _description_
        hue : _type_, optional
            _description_, by default None
        hue_order : _type_, optional
            _description_, by default None
        xtick_rot : int, optional
            _description_, by default 30
        ax : _type_, optional
            _description_, by default None
        """
        if ax is None:
            ax = plt.gca()

        self.plot_kw = dict(data=data, x=x, y=y, hue=hue, hue_order=hue_order, ax=ax)

        # Set up rotation - note that to ensure right justification of all text,
        # we will need to re-set some of these properties again for each plot
        self.xtick_rot = xtick_rot
        if xtick_rot is not None:
            ax.tick_params(axis="x", labelrotation=xtick_rot)

    def violinplot_sd(self, split=True, palette=None, scale="width", **kwargs):
        sns.violinplot(
            **self.plot_kw,
            split=split,
            inner="quartile",
            linewidth=0,
            palette=palette,
            saturation=1,
            cut=False,
            scale=scale,
            **kwargs,
        )
        for p in self.plot_kw["ax"].lines:
            p.set_linestyle("-")
            p.set_linewidth(0.5)  # Sets the thickness of the quartile lines
            p.set_color("white")  # Sets the color of the quartile lines
            p.set_alpha(1)

        self.plot_kw["ax"].legend("", frameon=False)

        # Right align xticklabels
        xlabels = self.plot_kw["ax"].get_xticklabels()
        self.plot_kw["ax"].set_xticklabels(xlabels,
                                           rotation=self.xtick_rot,
                                           ha="right")

        return self

    def boxplot_sd(self, palette=None, sep=0.9, inherit_whisker_color=False, **kwargs):
        ax = sns.boxplot(
            **self.plot_kw,
            linewidth=0,
            palette=palette,
            saturation=1,
            showfliers=False,
            medianprops=dict(color="white", linewidth=0.6, solid_capstyle="butt"),
            boxprops=dict(edgecolor="w", linewidth=0),
            whiskerprops=dict(color="k", linewidth=0.5, solid_capstyle="butt"),
            showcaps=True,
            capprops=dict(color="k"),
            # capwidths=0.2,
            **kwargs,
        )

        if inherit_whisker_color:
            box_patches = [
                patch for patch in ax.patches if type(patch) == mpl.patches.PathPatch
            ]

            n_boxes = len(box_patches)
            lines_per_box = len(ax.lines) // n_boxes

            for i, patch in enumerate(box_patches):
                box_color = patch.get_facecolor()

                # whisker_lines = [
                #     ax.lines[i * lines_per_box],
                #     ax.lines[i * lines_per_box+1],
                # ]

                whisker_lines = ax.lines[i * lines_per_box : (i + 1) * lines_per_box]
                whisker_lines = [whisker_lines[0], whisker_lines[1]]

                for line in whisker_lines:
                    line.set_color(box_color)

        for c in ax.get_children():
            # searching for PathPatches
            if isinstance(c, mpl.patches.PathPatch):
                # getting current width of box:
                p = c.get_path()
                verts = p.vertices
                verts_sub = verts[:-1]
                xmin = np.min(verts_sub[:, 0])
                xmax = np.max(verts_sub[:, 0])
                xmid = 0.5 * (xmin + xmax)
                xhalf = 0.5 * (xmax - xmin)

                # setting new width of box
                xmin_new = xmid - sep * xhalf
                xmax_new = xmid + sep * xhalf
                verts_sub[verts_sub[:, 0] == xmin, 0] = xmin_new
                verts_sub[verts_sub[:, 0] == xmax, 0] = xmax_new

                # setting new width of median line
                for l in ax.lines:
                    if np.all(l.get_xdata() == [xmin, xmax]):
                        l.set_xdata([xmin_new, xmax_new])

        yticks = ax.get_yticks()
        ax.set_yticks(yticks)

        self.plot_kw["ax"].legend("", frameon=False)

        # Right align xticklabels
        xlabels = self.plot_kw["ax"].get_xticklabels()
        self.plot_kw["ax"].set_xticklabels(xlabels,
                                           rotation=self.xtick_rot,
                                           ha="right")

        return self

    def boxplot_sd2(self, palette=None, sep=0.9, zorder=2, **kwargs):
        ax = sns.boxplot(
            **self.plot_kw,
            linewidth=0.4,
            palette=palette,
            saturation=1,
            showfliers=False,
            **kwargs,
        )

        box_patches = [
            patch for patch in ax.patches if type(patch) == mpl.patches.PathPatch
        ]

        n_boxes = len(box_patches)
        lines_per_box = len(ax.lines) // n_boxes

        for i, patch in enumerate(box_patches):
            box_color = patch.get_facecolor()
            patch.set_facecolor("None")
            patch.set_edgecolor(box_color)
            patch.set_zorder(zorder)

            # whisker_lines = [
            #     ax.lines[i * lines_per_box],
            #     ax.lines[i * lines_per_box+1],
            # ]

            whisker_lines = ax.lines[i * lines_per_box : (i + 1) * lines_per_box]
            # whisker_lines = [whisker_lines[0], whisker_lines[1]]

            for line in whisker_lines:
                line.set_color(box_color)
                line.set_zorder(zorder)

        for c in ax.get_children():
            # searching for PathPatches
            if isinstance(c, mpl.patches.PathPatch):
                # getting current width of box:
                p = c.get_path()
                verts = p.vertices
                verts_sub = verts[:-1]
                xmin = np.min(verts_sub[:, 0])
                xmax = np.max(verts_sub[:, 0])
                xmid = 0.5 * (xmin + xmax)
                xhalf = 0.5 * (xmax - xmin)

                # setting new width of box
                xmin_new = xmid - sep * xhalf
                xmax_new = xmid + sep * xhalf
                verts_sub[verts_sub[:, 0] == xmin, 0] = xmin_new
                verts_sub[verts_sub[:, 0] == xmax, 0] = xmax_new

                # setting new width of median line
                for l in ax.lines:
                    if np.all(l.get_xdata() == [xmin, xmax]):
                        l.set_xdata([xmin_new, xmax_new])

        self.plot_kw["ax"].legend("", frameon=False)

        # Right align xticklabels
        xlabels = self.plot_kw["ax"].get_xticklabels()
        self.plot_kw["ax"].set_xticklabels(xlabels,
                                           rotation=self.xtick_rot,
                                           ha="right")

        return self

    def stripbarplot_sd(self, palette=None, dodge=True, **kwargs):
        ax = sns.stripplot(
            **self.plot_kw,
            palette=palette,
            edgecolor="w",
            linewidth=0.3,
            size=3,
            dodge=dodge,
            **kwargs,
        )
        sns.barplot(
            **self.plot_kw,
            ci=None,
            facecolor="w",
            linewidth=0.5,
            edgecolor=".2",
            **kwargs,
        )
        ax.legend("", frameon=False)

        return self

    def stripbarlineplot_sd(self, palette=None, dodge=0.1, **kwargs):
        ax = sns.lineplot(
            **self.plot_kw,
            palette=palette,
            units="session",
            estimator=None,
            lw=0.25,
            alpha=0.25,
            # sort=True,
            # **kwargs,
        )
        sns.stripplot(
            **self.plot_kw,
            palette=palette,
            edgecolor="w",
            linewidth=0.2,
            size=2,
            dodge=dodge,
            jitter=True,
            # alpha=0.8,
            # **kwargs,
        )
        sns.barplot(
            **self.plot_kw,
            ci=None,
            facecolor="w",
            linewidth=0.5,
            edgecolor=".2",
            # **kwargs,
        )

        lines = [line for line in ax.lines if line.get_xdata().size > 0]
        n_lines_per_hue = len(lines) // 2

        # for line in lines[:8]:
        #     x = line.get_xdata()
        #     line.set_xdata(x - 0.2)

        # for line in lines[8:]:
        #     x = line.get_xdata()
        #     line.set_xdata(x + 0.2)

        if len(palette) == 2:
            for line in ax.lines:
                line_color = line.get_color()
                lw = line.get_linewidth()
                x = line.get_xdata()
                if lw == 0.25:
                    if line_color == palette[0]:
                        line.set_xdata(x - 0.2)
                        # line.set_zorder(zorder - 10)

                    if line_color == palette[1]:
                        line.set_xdata(x + 0.2)
                        # line.set_zorder(zorder - 10)

        self.plot_kw["ax"].legend("", frameon=False)

        # Right align xticklabels
        xlabels = self.plot_kw["ax"].get_xticklabels()
        self.plot_kw["ax"].set_xticklabels(xlabels,
                                           rotation=self.xtick_rot,
                                           ha="right")

        return self

    def striplineplot_sd(self, palette=None, dodge=0.1, zorder=2, units="session", **kwargs):
        ax = sns.lineplot(
            **self.plot_kw,
            palette=palette,
            units=units,
            estimator=None,
            lw=0.25,
            alpha=0.2,
            # sort=True,
            # **kwargs,
        )
        sns.stripplot(
            **self.plot_kw,
            palette=palette,
            edgecolor="w",
            linewidth=0.2,
            size=2,
            dodge=dodge,
            jitter=True,
            zorder=zorder,
            # alpha=0.5,
            **kwargs,
        )

        if palette is not None:
            if len(palette) == 1:
                color = palette[0]
                for line in ax.lines:
                    if line.get_linewidth() == 0.25:
                        line.set_color(color)
                        line.set_zorder(zorder - 10)
            if len(palette) == 2:
                for line in ax.lines:
                    line_color = line.get_color()
                    lw = line.get_linewidth()
                    x = line.get_xdata()
                    if lw == 0.25:
                        if line_color == palette[0]:
                            try:  # New version of matplotlib is catching wrong lines, bugfix
                                line.set_xdata(x - 0.2)
                            except TypeError:
                                pass
                            line.set_zorder(zorder - 10)

                        if line_color == palette[1]:
                            try:
                                line.set_xdata(x + 0.2)
                            except TypeError:
                                pass
                            line.set_zorder(zorder - 10)

        self.plot_kw["ax"].legend("", frameon=False)

        # Right align xticklabels
        xlabels = self.plot_kw["ax"].get_xticklabels()
        self.plot_kw["ax"].set_xticklabels(xlabels,
                                           rotation=self.xtick_rot,
                                           ha="right")

        return self

    def stat_anot_sd(
        self,
        stat_within=None,
        stat_across=None,
        alpha_within: float or list = 0.05,
        alpha_across: float or list = 0.05,
        alpha_trend_within: float or None = 0.05,
        alpha_trend_across: float or None = 0.10,
        fontsize=8,
        verbose=False,
        pair_names=["NSD", "SD"],
        **kwargs,
    ):
        ax = self.plot_kw["ax"]
        stat_kw["fontsize"] = fontsize

        results_list = []
        if stat_across is not None:
            # stat_kw["pvalue_thresholds"] = [[alpha_across, "*"], [1, "ns"]]
            alpha_across = [alpha_across] if isinstance(alpha_across, float) else alpha_across
            pval_thresh = [[a, '*' * (ida + 1)] for ida, a in enumerate(alpha_across)]
            if alpha_trend_across is not None:
                pval_thresh.append([alpha_trend_across, "#"])
            pval_thresh.append([1, "ns"])
            stat_kw["pvalue_thresholds"] = pval_thresh
            ax2 = ax.inset_axes([0, 0.9, 1, 0.15])
            self.plot_kw["ax"] = ax2
            ax2.set_axis_off()

            orders = self.plot_kw["data"].zt.unique()
            if callable(stat_across):
                custom_long_name = stat_across.__name__
                custom_short_name = stat_across.__name__
                stat_across = StatTest(stat_across, custom_long_name, custom_short_name)

            # Across groups
            pair_name1, pair_name2 = pair_names
            # pairs = [((_, "NSD"), (_, "SD")) for _ in orders]
            pairs = [((_, pair_name1), (_, pair_name2)) for _ in orders]
            if ("0-2.5" in orders) & ("5-7.5" in orders):
                pairs = pairs + [(("0-2.5", pair_name1), ("5-7.5", pair_name2))]
            elif ("ZT 0-2.5" in orders) & ("ZT 5-7.5" in orders):
                pairs = pairs + [(("ZT 0-2.5", pair_name1), ("ZT 5-7.5", pair_name2))]
            elif ("0-1" in orders) & ("5-6" in orders):
                pairs = pairs + [(("0-1", pair_name1), ("5-6", pair_name2))]
            elif ("ZT 0-1" in orders) & ("ZT 5-6" in orders):
                pairs = pairs + [(("ZT 0-1", pair_name1), ("ZT 5-6", pair_name2))]
            annotator = Annotator(pairs=pairs, **self.plot_kw, order=orders)
            annotator.configure(test=stat_across, **stat_kw, color="k", verbose=verbose)
            annotator.apply_and_annotate()
            results_list.append(get_stats_from_annotation(annotator.annotations, **kwargs))
            annotator.reset_configuration()

        if stat_within is not None:
            # stat_kw["pvalue_thresholds"] = [[alpha_within, "*"], [1, "ns"]]
            alpha_within = [alpha_within] if isinstance(alpha_within, float) else alpha_within
            pval_thresh = [[a, '*' * (ida + 1)] for ida, a in enumerate(alpha_within)]
            if alpha_trend_within is not None:
                pval_thresh.append([alpha_trend_within, "#"])
            pval_thresh.append([1, "ns"])
            stat_kw["pvalue_thresholds"] = pval_thresh
            orders = self.plot_kw["data"].zt.unique()
            if callable(stat_within):
                custom_long_name = stat_within.__name__
                custom_short_name = stat_within.__name__
                stat_within = StatTest(stat_within, custom_long_name, custom_short_name)

            # Within groups
            yshift = 0
            # for i, g in enumerate(["NSD", "SD"]):
            for i, g in enumerate(pair_names):
                ax2 = ax.inset_axes([0.1, 1.1 + yshift, 0.9, 0.3])
                ax2.axis("off")
                self.plot_kw["ax"] = ax2

                # pairs = [
                #     (("0-2.5", g), ("2.5-5", g)),
                #     (("2.5-5", g), ("5-7.5", g)),
                #     (("0-2.5", g), ("5-7.5", g)),
                # ]
                order_pairs = list(itertools.combinations(orders, 2))
                pairs = [((p[0], g), (p[1], g)) for p in order_pairs]
                annotator = Annotator(pairs=pairs, **self.plot_kw, order=orders)
                annotator.configure(
                    test=stat_within, **stat_kw, color=colors_sd(1)[i], verbose=verbose
                )
                annotator.apply_and_annotate()
                results_list.append(get_stats_from_annotation(annotator.annotations, **kwargs))
                annotator.reset_configuration()
                yshift += 0.3


        return results_list

    def correct_order(self, order):
        try:
            if "0-1" in order:
                req_order = ["PRE", "MAZE", "0-1", "4-5", "5-6"]
                indx = np.array([req_order.index(i) for i in order])
                sort_indx = np.argsort(indx)
            else:
                req_order = ["PRE", "MAZE", "0-2.5", "2.5-5", "5-7.5"]
                indx = np.array([req_order.index(i) for i in order])
                sort_indx = np.argsort(indx)
        except ValueError:  # Fix if prepending "ZT" to each post epoch
            if "ZT 0-1" in order:
                req_order = ["PRE", "MAZE", "ZT 0-1", "ZT 4-5", "ZT 5-6"]
                indx = np.array([req_order.index(i) for i in order])
                sort_indx = np.argsort(indx)
            else:
                req_order = ["PRE", "MAZE", "ZT 0-2.5", "ZT 2.5-5", "ZT 5-7.5"]
                indx = np.array([req_order.index(i) for i in order])
                sort_indx = np.argsort(indx)

        return list(np.array(order)[sort_indx])

    def stat_anot(
        self,
        stat_within,
        alpha_within: float or list=0.05,
        alpha_trend: float or None = 0.1,
        stat_unequal=None,
        fontsize=8,
        verbose=False,
        **kwargs,  # to get_stats_from_annotations
    ):
        stat_kw["fontsize"] = fontsize
        ax = self.plot_kw["ax"]
        alpha_within = [alpha_within] if isinstance(alpha_within, float) else alpha_within
        pval_thresh = [[a, '*' * (ida + 1)] for ida, a in enumerate(alpha_within)]
        if alpha_trend is not None:
            pval_thresh.append([alpha_trend, "#"])

        pval_thresh.append([1, "ns"])
        stat_kw["pvalue_thresholds"] = pval_thresh
        orders = self.correct_order(self.plot_kw["data"].zt.unique())
        order_pairs = list(itertools.combinations(orders, 2))

        ax2 = ax.inset_axes([0, 0.9, 1, 0.6])
        ax2.axis("off")
        self.plot_kw["ax"] = ax2

        results_list = []
        if stat_unequal is not None:
            data = self.plot_kw["data"]
            unequal_bool = np.zeros(len(order_pairs)).astype("bool")
            for i, pair in enumerate(order_pairs):
                if len(data[data.zt == pair[0]]) != len(data[data.zt == pair[1]]):
                    unequal_bool[i] = True

            if callable(stat_unequal):
                custom_long_name = stat_unequal.__name__
                custom_short_name = stat_unequal.__name__
                stat_unequal = StatTest(stat_unequal, custom_long_name, custom_short_name)

            unequal_pairs = [
                order_pairs[i] for i, cond in enumerate(unequal_bool) if cond == True
            ]

            if len(unequal_pairs) > 0:
                annotator = Annotator(
                    pairs=unequal_pairs,
                    **self.plot_kw,
                    order=orders,
                )
                annotator.configure(
                    test=stat_unequal, **stat_kw, color="k", verbose=verbose
                )
                annotator.apply_and_annotate()
                results_list.append(get_stats_from_annotation(annotator.annotations, **kwargs))
                annotator.reset_configuration()

                order_pairs = [
                    order_pairs[i] for i, cond in enumerate(unequal_bool) if cond == False
                ]

        if callable(stat_within):
            custom_long_name = stat_within.__name__
            custom_short_name = stat_within.__name__
            stat_within = StatTest(stat_within, custom_long_name, custom_short_name)

        if len(order_pairs) > 0:
            # order_pairs = list(itertools.combinations(orders, 2))
            # pairs = [(p[0], p[1]) for p in order_pairs]
            annotator = Annotator(pairs=order_pairs, **self.plot_kw, order=orders)
            annotator.configure(test=stat_within, **stat_kw, color="k", verbose=verbose)
            annotator.apply_and_annotate()
            results_list.append(get_stats_from_annotation(annotator.annotations, **kwargs))
            annotator.reset_configuration()

        return results_list

    def _remove_legend(self):
        self.plot_kw["ax"].legend("", frameon=False)

    def areaplot(self, alpha=0.5, **kwargs):
        sns.lineplot(**self.plot_kw, **kwargs)
        ax = self.plot_kw["ax"]
        for line in ax.lines:
            x, y = line.get_xydata().T
            ax.fill_between(x, 0, y, color=line.get_color(), alpha=alpha, ec=None)

        self._remove_legend()


def get_nsd_vs_sd_df(data: pd.DataFrame, block_size: float or int in [1, 2.5] = 2.5):
    zt_prepend = ('ZT 0-2.5' in data.zt.unique()) or ('ZT 0-1' in data.zt.unique())
    if block_size == 2.5:
        if zt_prepend:
            df = data[data.zt.isin(["ZT 0-2.5", "ZT 2.5-5", "ZT 5-7.5"])].copy()
            df.drop(df[(df.zt == "ZT 0-2.5") & (df.grp == "SD")].index, inplace=True)
            df.drop(df[(df.zt == "ZT 5-7.5") & (df.grp == "NSD")].index, inplace=True)
            df.loc[(df.zt == "ZT 0-2.5") & (df.grp == "NSD"), "zt"] = "ZT 0-2.5 vs 5-7.5"
            df.loc[(df.zt == "ZT 5-7.5") & (df.grp == "SD"), "zt"] = "ZT 0-2.5 vs 5-7.5"
        else:
            df = data[data.zt.isin(["0-2.5", "2.5-5", "5-7.5"])].copy()
            df.drop(df[(df.zt == "0-2.5") & (df.grp == "SD")].index, inplace=True)
            df.drop(df[(df.zt == "5-7.5") & (df.grp == "NSD")].index, inplace=True)
            df.loc[(df.zt == "0-2.5") & (df.grp == "NSD"), "zt"] = "0-2.5 vs 5-7.5"
            df.loc[(df.zt == "5-7.5") & (df.grp == "SD"), "zt"] = "0-2.5 vs 5-7.5"
    else:  # For 1h blocks
        if zt_prepend:
            df = data[data.zt.isin(["ZT 0-1", "ZT 4-5", "ZT 5-6"])].copy()
            df.drop(df[(df.zt == "ZT 0-1") & (df.grp == "SD")].index, inplace=True)
            df.drop(df[(df.zt == "ZT 5-6") & (df.grp == "NSD")].index, inplace=True)
            df.loc[(df.zt == "ZT 0-1") & (df.grp == "NSD"), "zt"] = "ZT 0-1 vs 5-6"
            df.loc[(df.zt == "ZT 5-6") & (df.grp == "SD"), "zt"] = "ZT 0-1 vs 5-6"
        else:
            df = data[data.zt.isin(["0-1", "4-5", "5-6"])].copy()
            df.drop(df[(df.zt == "0-1") & (df.grp == "SD")].index, inplace=True)
            df.drop(df[(df.zt == "5-6") & (df.grp == "NSD")].index, inplace=True)
            df.loc[(df.zt == "0-1") & (df.grp == "NSD"), "zt"] = "0-1 vs 5-6"
            df.loc[(df.zt == "5-6") & (df.grp == "SD"), "zt"] = "0-1 vs 5-6"

    return df


def get_stats_from_annotation(annotation_in, prepend=()):
    """Grabs stats from a list of annotator objects and puts them into csv from annotator
    set prepend to add a list of items to the beginning of results"""
    results = []
    if isinstance(annotation_in, statannotations.Annotation.Annotation):
        cmp1 = annotation_in.structs[0]["label"]
        cmp2 = annotation_in.structs[1]["label"]
        stats_str = [aa.split(" ") for aa in annotation_in.formatted_output.split(":")]
        test_used = stats_str[0][0]
        pval_str = stats_str[1][0]
        test_stat = stats_str[1][1].split("=")[1]

        results.append([*prepend, cmp1, cmp2, test_used, pval_str, test_stat])
    elif isinstance(annotation_in, list):
        for a in annotation_in:
            results.append(get_stats_from_annotation(a, prepend=prepend)[0])

    return results


def stats_to_df(results_list, prepend=()):
    """Converts list of stats from get_stats_from_annotation to dataframe"
    :param results_list = output of get_stats_from_annotation
    :param prepend: list or tuple that matches input to get_stats_from_annotation"""

    columns = list(prepend)
    columns.extend(["comp1", "comp2", "test", "pval", "test_stat"])
    stats_df = pd.DataFrame(flatten(flatten(results_list)), columns=columns)

    return stats_df

def filt_to_1h_blocks(filt_in):
    """Adjusts filter in filter_stats_df from 2.5 to 1h blocks"""
    filt_out = deepcopy(filt_in)

    # Replace everything -returns a flattened list
    filt_out = [sub2.replace("ZT 0-2.5", "ZT 0-1") for sub1 in filt_out for sub2 in sub1]
    filt_out = [sub1.replace("ZT 2.5-5", "ZT 4-5") for sub1 in filt_out]
    filt_out = [sub1.replace("ZT 5-7.5", "ZT 5-6") for sub1 in filt_out]
    if np.any(["5-7.5" in sub1 for sub1 in filt_out]):  # For NSD vs SD comparisons
        filt_out = [sub1.replace("5-7.5", "5-6") for sub1 in filt_out]

    # Unflatten into list of len = 2 lists
    filt_out2 = []
    for ide, entry in enumerate(filt_out):
        if np.mod(ide, 2) == 0:
            grp = [entry]
        elif np.mod(ide, 2) == 1:
            grp.append(entry)
            filt_out2.append(grp)

    return filt_out2


def filter_stats_df(stats_df: pd.DataFrame, figure: str):
    """Keeps only relevant comparisons from results_df which calculates everything"""
    if figure in ["1","EDF6A"]:
        filt = {"within": [["PRE", "MAZE"], ["MAZE", "ZT 0-2.5"], ["ZT 0-2.5", "ZT 2.5-5"], ["ZT 2.5-5", "ZT 5-7.5"],
                           ["PRE", "ZT 0-2.5"], ["ZT 0-2.5", "ZT 5-7.5"]],
                "across": [["ZT 2.5-5_NSD", "ZT 2.5-5_SD"], ["ZT 0-2.5 vs 5-7.5_NSD", "ZT 0-2.5 vs 5-7.5_SD"]]}
    elif figure in ["EDF2K"]:
        filt = {"within": [["PRE", "MAZE"], ["MAZE", "ZT 0-2.5"], ["ZT 0-2.5", "ZT 2.5-5"], ["ZT 2.5-5", "ZT 5-7.5"],
                           ["PRE", "ZT 0-2.5"], ["ZT 0-2.5", "ZT 5-7.5"], ["PRE", "ZT 5-7.5"]],
                "across": [["ZT 2.5-5_NSD", "ZT 2.5-5_SD"], ["ZT 0-2.5 vs 5-7.5_NSD", "ZT 0-2.5 vs 5-7.5_SD"]]}
    elif figure in ["2", "EDF3", "EDF6B"]:
        filt = {"within": [["PRE", "MAZE"], ["MAZE", "ZT 0-2.5"], ["ZT 0-2.5", "ZT 2.5-5"], ["ZT 2.5-5", "ZT 5-7.5"],
                           ["ZT 0-2.5", "ZT 5-7.5"]],
                "across": [["ZT 2.5-5_NSD", "ZT 2.5-5_SD"], ["ZT 0-2.5 vs 5-7.5_NSD", "ZT 0-2.5 vs 5-7.5_SD"]]}
    elif figure in ["2E", "EDF3F"]:
        filt = {"across": [["PRE", "PRE"], ["MAZE", "MAZE"], ["ZT 0-2.5", "ZT0-2.5"], ["ZT 2.5-5", "ZT 2.5-5"],
                           ["ZT 5-7.5", "ZT 5-7.5"],
                           ["ZT 0-2.5", "ZT 5-7.5"]]}
    elif figure in ["3", "EDF6C"]:
        filt = {"within": [["ZT 0-2.5", "ZT 2.5-5"], ["ZT 2.5-5", "ZT 5-7.5"]],
                "across": [["ZT 0-2.5", "ZT0-2.5"], ["ZT 2.5-5", "ZT 2.5-5"],
                           ["ZT 5-7.5", "ZT 5-7.5"], ["ZT 0-2.5", "ZT 5-7.5"]]}
    elif figure in ["4", "EDF6D", "EDF7B"]:
        filt = {"within": [["PRE_NSD", "MAZE_NSD"], ["MAZE_NSD", "ZT 0-2.5_NSD"], ["ZT 0-2.5_NSD", "ZT 2.5-5_NSD"],
                           ["ZT 2.5-5_NSD", "ZT 5-7.5_NSD"], ["PRE_NSD", "ZT 0-2.5_NSD"],
                           ["PRE_SD", "MAZE_SD"], ["MAZE_SD", "ZT 0-2.5_SD"], ["ZT 0-2.5_SD", "ZT 2.5-5_SD"],
                           ["ZT 2.5-5_SD", "ZT 5-7.5_SD"], ["PRE_SD", "ZT 0-2.5_SD"]],
                "across": [["PRE_NSD", "PRE_SD"], ["MAZE_NSD", "MAZE_SD"], ["ZT 0-2.5_NSD", "ZT0-2.5_SD"],
                           ["ZT 2.5-5_NSD", "ZT 2.5-5_SD"], ["ZT 5-7.5_NSD", "ZT 5-7.5_SD"],
                           ["ZT 0-2.5_NSD", "ZT 5-7.5_SD"]]}
    elif figure in ["EDF7C", "EDF7D", "EDF7E"]:
        filt = {"within": [["PRE", "MAZE"], ["MAZE", "ZT 0-2.5"], ["ZT 0-2.5", "ZT 2.5-5"], ["ZT 2.5-5", "ZT 5-7.5"],
                           ["PRE", "ZT 0-2.5"]],
                "across": [["ZT 2.5-5_NSD", "ZT 2.5-5_SD"], ["ZT 0-2.5 vs 5-7.5_NSD", "ZT 0-2.5 vs 5-7.5_SD"]]}

    if "EDF6" in figure:  # Change to 1h nomenclature for figure 6
        filt["within"] = filt_to_1h_blocks(filt["within"])
        filt["across"] = filt_to_1h_blocks(filt["across"])

    if "within" in filt.keys():
        if figure in ["3", "EDF6C"]:
            within_bool = stats_df.grp == "SD"
        elif figure in ["4", "EDF6D", "EDF7B"]:
            within_bool = np.ones_like(stats_df.comp1, dtype=bool)
        else:
            within_bool = (stats_df.grp == "NSD") | (stats_df.grp == "SD")
        comp_bool = np.zeros_like(within_bool, dtype=bool)
        for (comp1, comp2) in filt["within"]:
            comp_bool = comp_bool | ((stats_df.comp1 == comp1) & (stats_df.comp2 == comp2))
        within_bool = within_bool & comp_bool

    else:
        within_bool = stats_df.grp == "blah"  # Don't collect any within group stats

    # across_bool = stats_df.grp == "b/w"
    across_bool = np.ones_like(within_bool)
    comp_bool = np.zeros_like(across_bool, dtype=bool)
    for (comp1, comp2) in filt["across"]:
        comp_bool = comp_bool | ((stats_df.comp1 == comp1) & (stats_df.comp2 == comp2))
    across_bool = across_bool & comp_bool

    return stats_df[within_bool | across_bool]

def add_parametric_extras(df: pd.DataFrame, results_df_in: pd.DataFrame,
                          metric: str, merge_thresh: float = 0.001):
    """Adds in effect size ("Cohens's-D), 95% CI, and dof for parametric tests (t-tests) by re-running
    stats with pingouin.
    :params:  see below for usage of df, results_df_in, and metric
    :param merge_thresh: float, difference between test statistics must be within this tolerance to merge in extras.
    example:
    plotter = Plotter(data=delta_rate_df, x="zt", y="delta_rate", hue="grp", hue_order=["NSD", "SD"])
    results_list = Plotter.stripbarlineplot_sd(..., stat_across="t-test_welch, stat_within="t-test_paired")
    results_df = stats_to_df(results_list)
    add_parametric_extras(delt[
    a_rate_df, results_df, "delta_rate")
    """
    pg_stats_list = []
    for idr, row in results_df_in.iterrows():

        # Get appropriate comparisons from results_df
        try:
            t1, grp1 = row.comp1.split("_")
            t2, grp2 = row.comp2.split("_")
            grp_from_df = False
        except ValueError:
            grp1, grp2 = row.grp, row.grp
            t1, t2 = row.comp1, row.comp2
            grp_from_df = True



        # Check if paired and if not set correction to "Welch" for unequal variance
        if grp1 != grp2:
            paired, welch = False, True
        else:
            paired, welch = True, False

        try:
            n1 = ((df.grp == grp1) & (df.zt == t1)).sum()
            n2 = ((df.grp == grp2) & (df.zt == t2)).sum()
            if paired and n1 != n2:
                paired = False

            pg_stats_list.append(
                pg.ttest(df[(df.grp == grp1) & (df.zt == t1)][metric], df[(df.grp == grp2) & (df.zt == t2)][metric],
                         paired=paired, correction=welch))
        except AssertionError:
            print(f"error calculating stats for index={idr}. Do by hand!")
            pg_stats_list.append(pd.Series(data=np.nan))

    # Make into a dataframe
    pg_results_df = pd.concat(pg_stats_list, axis=0).reset_index()
    pg_results_df.insert(0, "comp1", results_df_in.comp1.values)
    pg_results_df.insert(1, "comp2", results_df_in.comp2.values)
    print(df.keys())
    if "state" in df.keys() or "brainstate" in df.keys():
        pg_results_df.insert(0, "state", results_df_in.state.values)
    if grp_from_df and ("group" in df.keys() or "grp" in df.keys()):
        pg_results_df.insert(0, "grp", results_df_in.grp.values)
    if "feature" in results_df_in.keys():
        pg_results_df.insert(0, "feature", results_df_in.feature.values)


    merge_bool = (((results_df_in["test_stat"].astype(float) - pg_results_df["T"]) / pg_results_df[
        "T"]).abs() < merge_thresh).all()

    # Last, merge in Cohen's D, 95% CI, and dof from pingouin if test-statistics are the "same" (within merge_tresh above)
    if merge_bool:
        results_df_out = deepcopy(results_df_in)
        results_df_out["CI95%"] = pg_results_df["CI95%"]
        results_df_out["Cohen's-d"] = pg_results_df["cohen-d"]
        results_df_out["dof"] = pg_results_df["dof"]

    else:
        results_df_out = pg_results_df
        print(
            "test-statistics are off by more than merge_thresh - returning pingouin values - compare to results_df_in and re-run")

    return results_df_out

def get_nsd_vs_sd_df_by_state(data: pd.DataFrame):
    """"Parses dataframe for comparison between NSD 0-2.5h vs SD 5-7.5h NREM states
    and 2-5.5h NSD vs. SD WAKE states"""

    # Grab appropriate keys to use
    state_key = "brainstate" if "brainstate" in data.keys() else "state"
    wake_key = "WK" if "WK" in data[state_key].unique() else "WAKE"

    # Grab appropriately formatted ZT string
    nrem_drop_str, wake_drop_str = "", ""
    if "2.5-5" in data.zt.unique():
        nrem_drop_str, wake_drop_str = "2.5-5", "0-2.5 vs 5-7.5"
    elif "ZT 2.5-5" in data.zt.unique():
        nrem_drop_str, wake_drop_str = "ZT 2.5-5", "ZT 0-2.5 vs 5-7.5"
    else:
        ValueError("data input zt field is improperly formatted.")

    # Grab NREM and drop 2.5-5 hour session - leaves only 0-2.5 NSD and 5-7.5 SD
    df_nrem = get_nsd_vs_sd_df(data[data[state_key] == "NREM"])
    df_nrem.drop(df_nrem[(df_nrem.zt == nrem_drop_str)].index, inplace=True)

    # Grab WAKE and drop the 0-2.5 vs 5-7.5 designation
    df_wake = get_nsd_vs_sd_df(data[data[state_key] == wake_key])
    df_wake.drop(df_wake[df_wake.zt == wake_drop_str].index, inplace=True)

    return pd.concat((df_nrem, df_wake))


sns_violin_kw = dict(
    palette=colors_sd(1),
    saturation=1,
    linewidth=0.4,
    cut=True,
    split=False,
    inner="box",
    showextrema=False,
    # showmeans=True,
)

colors = ["#999897", "#f07067"] + ["#424242", "#eb4034"] * 2 + ["#424242", "#48bdf7"]


def violinplotx(
    data,
    x,
    y,
    ax=None,
    stat_anot=False,
    stat_test=None,
    color="k",
    xtick_rot=30,
    **kwargs,
):
    if ax is None:
        ax = plt.gca()

    plot_kw = dict(data=data, x=x, y=y, ax=ax)
    sns.violinplot(
        **plot_kw,
        inner="quartile",
        linewidth=0,
        color=color,
        # colors=colors,
        # scale="width",
        saturation=1,
        cut=True,
        **kwargs,
    )
    for p in ax.lines:
        p.set_linestyle("-")
        p.set_linewidth(0.5)  # Sets the thickness of the quartile lines
        p.set_color("white")  # Sets the color of the quartile lines
        p.set_alpha(1)

    ax.legend("", frameon=False)
    if xtick_rot is not None:
        ax.tick_params(axis="x", labelrotation=xtick_rot)
    return ax


def tn_violinplot(
    data,
    x,
    y,
    ax=None,
    stat_anot=False,
    stat_test=None,
    xtick_rot=30,
    split=True,
    **kwargs,
):
    if ax is None:
        ax = plt.gca()

    plot_kw = dict(data=data, x=x, y=y, ax=ax)
    sns.violinplot(
        **plot_kw,
        split=split,
        inner="quartile",
        linewidth=0,
        # palette=colors_sd(1),
        # colors=colors,
        # scale="width",
        saturation=1,
        cut=True,
        **kwargs,
    )
    for p in ax.lines:
        p.set_linestyle("-")
        p.set_linewidth(0.8)  # Sets the thickness of the quartile lines
        p.set_color("white")  # Sets the color of the quartile lines
        p.set_alpha(1)

    if stat_anot:
        orders = data[x].unique()
        if stat_test is None:
            stat_test = "t-test_welch"

        # Across groups
        pairs = [
            ("pre", "post1"),
            ("pre", "post2"),
            ("maze1", "maze2"),
            ("post1", "post2"),
        ]
        annotator = Annotator(pairs=pairs, **plot_kw, order=orders)
        annotator.configure(test=stat_test, **stat_kw, color="k")
        annotator.apply_and_annotate()
        annotator.reset_configuration()

    ax.legend("", frameon=False)
    if xtick_rot is not None:
        ax.tick_params(axis="x", labelrotation=xtick_rot)
    return ax


def stripplot(
    data,
    x,
    y,
    hue="grp",
    hue_order=["NSD", "SD"],
    ax=None,
    dodge=True,
    size=3,
    stat_anot=False,
    stat_test=None,
    xtick_rot=30,
    **kwargs,
):
    if ax is None:
        ax = plt.gca()

    plot_kw = dict(data=data, x=x, y=y, hue=hue, hue_order=hue_order, ax=ax)
    sns.stripplot(
        **plot_kw,
        palette=colors_sd(1),
        edgecolor="w",
        linewidth=0.3,
        size=size,
        dodge=dodge,
        **kwargs,
    )

    if stat_anot:
        orders = data.zt.unique()
        if stat_test is None:
            stat_test = "t-test_welch"

        # Across groups
        pairs = [((_, "NSD"), (_, "SD")) for _ in orders]
        annotator = Annotator(pairs=pairs, **plot_kw, order=orders)
        annotator.configure(test=stat_test, **stat_kw, color="#4AB33E")
        annotator.apply_and_annotate()
        annotator.reset_configuration()

    ax.legend("", frameon=False)
    if xtick_rot is not None:
        ax.tick_params(axis="x", labelrotation=xtick_rot)
        ax.set_xticklabels(ax.get_xticklabels, rotation=xtick_rot, ha="right")
    return ax

def add_zt_str(df: pd.DataFrame, zt_key="zt", epoch_str=("0-2.5", "2.5-5", "5-7.5")):
    """Fix zt strings to prepend ZT"""
    for epoch_name in epoch_str:
        df.loc[df[zt_key] == epoch_name, zt_key] = f"ZT {epoch_name}"

    return df
