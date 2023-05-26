import collections
import os
import argparse
import logging
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Logger object
logger = logging.getLogger("plot")
sns.set_context("paper", font_scale=1.25)
# sns.set_style("whitegrid")
sns.set_style("ticks")
# sns.set_palette("pastel")
MARKER_BASE = ["o", "^", "X", "s", "p", "P", ">", "*", "h", "H", "D", "d", "v", "<", "8", "x", "+",
               "|", "_", "."]
COLOR_BASE = ["r", "b", "g", "c", "m", "y", "k", "w"]
HATCH_BASE = ["", "/", "\\", "|", "-", "+", "x", "o", "O", ".", "*"]


def plot_mean_delay_chart(df, xlabel, ylabel, title, output, show=True):
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    ax.grid(linestyle="--")
    x, y1, y2, y3, z3 = df["nodes"], df[0.65], df[0.75], df[0.85], df["0.85.1"]
    # ax.plot(x, y1, label="DINNRS α=0.65", color="b", marker="o", markersize=8)
    # ax.plot(x, y2, label="DINNRS α=0.75", color="g", marker="^", markersize=8)
    ax.plot(x, y3, label="DINNRS α=0.85", color="r", marker=">", markersize=8)
    ax.plot(x, z3, label="MDHT α=0.85", color="b", marker="X", markersize=8)
    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.set_title(title)
    ax.legend()
    fig.savefig(output)
    if show:
        plt.show()


def plot_load_rate_chart(df, xlabel, ylabel, title, output, show=True):
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    ax.grid(linestyle="--")
    x, y1, y2 = df["rate"], df["total"], df["total.1"]
    # y use scientific notation
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
    ax.plot(x, y1, label="DINNRS α=0.85", color="r", marker="o", markersize=8)
    ax.plot(x, y2, label="MDHT α=0.85", color="b", marker="^", markersize=8)
    # ax.plot(x, y3, label="DINNRS α=0.85", color="r", marker=">", markersize=8)
    # ax.plot(x, z3, label="MDHT α=0.85", color="b", marker="X", markersize=8)
    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.set_title(title)
    ax.legend()
    fig.savefig(output)
    if show:
        plt.show()


def plot_internal_ratio(df, xlabel, ylabel, title, output, show=True):
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    ax.grid(linestyle="--")
    x, y1, y2 = df["rate"], df["internal-ratio"], df["internal-ratio.1"]
    # y use scientific notation
    # ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
    ax.plot(x, y1, label="DINNRS α=0.85", color="r", marker="o", markersize=8)
    ax.plot(x, y2, label="MDHT α=0.85", color="b", marker="^", markersize=8)
    # ax.plot(x, y3, label="DINNRS α=0.85", color="r", marker=">", markersize=8)
    # ax.plot(x, z3, label="MDHT α=0.85", color="b", marker="X", markersize=8)
    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.set_title(title)
    ax.legend()
    fig.savefig(output)
    if show:
        plt.show()


def plot_bar_chart(data, title, output, show=True):
    sns.set_style("white")
    # x_labels = ["Control", "Management", "Intermediary"]
    x_labels = ["level-1", "level-2", "level-3"]
    fig, ax = plt.subplots()
    # set figure size
    fig.set_size_inches(8, 6)
    x = [1, 2, 3]
    y = data
    ax.grid(linestyle="--", axis="y")
    ax.bar(x, y, width=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel("Domain type", fontsize=14)
    ax.set_ylabel("Resolve numbers in domains", fontsize=14)
    ax.set_title(title)
    fig.savefig(output)
    if show:
        plt.show()


def get_seq_hit_ratio(doc):
    seq_hit_ratio_pattern = r"\* SEQ_HIT_RATIO: \[(.*)\]"
    seq_hit_ratio_match = re.search(seq_hit_ratio_pattern, doc)
    if seq_hit_ratio_match:
        seq_hit_ratio_str = seq_hit_ratio_match.group(1)
        seq_hit_ratio = eval(seq_hit_ratio_str)
        return seq_hit_ratio
    else:
        print("No SEQ_HIT_RATIO data found in doc")


def get_avg_cache_hit_ratio(doc):
    avg_chr_pattern = r"MEAN: .*"
    avg_chr_match = re.search(avg_chr_pattern, doc)
    if avg_chr_match:
        avg_chr_str = avg_chr_match.group(0).split(":")[1].strip()
        avg_chr = eval(avg_chr_str)
        return avg_chr
    else:
        print("No average Cache hit ratio found in doc")


class P2(object):
    """
    Plot result in paper 2
    """

    def __init__(self, input_path, out_path):
        self.input_path = input_path
        self.out_path = out_path
        self.legend_map = {"popularity": "AC-POP", "random": "AC-RAND", "recommend": "AC-REC", "group": "AC-OPT"}

    def plot_cache_hit_ratio_seq_line_chart(self, xlabel, ylabel, title, show=True, date="0610"):
        fig, ax = plt.subplots()
        ax.grid(linestyle="--")
        # read file from path and get label from file name
        real_path = os.path.join(self.input_path, date)
        result_files = [os.path.join(real_path, k) for k in os.listdir(real_path)]

        print("result_files: {}".format(result_files))
        i = 0
        for file in result_files:
            label_name = os.path.basename(file).split(".")[0].split("_")[1]
            if label_name == "group" or label_name == "optimal":
                continue
            if label_name in self.legend_map:
                label_name = self.legend_map[label_name]
            with open(file, "r") as f:
                sr = get_seq_hit_ratio(f.read())
                df = pd.DataFrame(sr, columns=["time", "hit_ratio"])
                x = df["time"][::5]
                y = df["hit_ratio"][::5]
                # y use scientific notation
                ax.ticklabel_format(style="sci", axis="y", scilimits=(-2, 2))
                ax.plot(x, y, label=label_name, color=COLOR_BASE[i], marker=MARKER_BASE[i], markersize=5)
            i += 1

        ax.legend()
        ax.set_title(title)
        ax.set_xlabel(xlabel, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        fig.savefig(self.out_path + "/cache_hit_ratio_seq.pdf")
        if show:
            plt.show()

    def plot_avg_CHR_bar_group_chart(self, title, show=True):
        """
        Plot average cache hit ratio bar chart, x-axis is date, y-axis is average cache hit ratio,
        each bar is a group of four bars, each bar is a different algorithm
        """
        sns.set_palette("Set3")
        date_list = os.listdir(self.input_path)
        method_f_l = os.listdir(os.path.join(self.input_path, date_list[0]))
        res = collections.defaultdict(dict)
        for date in date_list:
            for method_f in method_f_l:
                method = os.path.basename(method_f).split(".")[0].split("_")[1]
                if method == "optimal":
                    continue
                if method in self.legend_map:
                    method = self.legend_map[method]
                with open(os.path.join(self.input_path, date, method_f), "r") as f:
                    avg_chr = get_avg_cache_hit_ratio(f.read())
                    res[date][method] = avg_chr

        # draw bar chart
        fig, ax = plt.subplots()
        ax.grid(linestyle="--")
        x = np.arange(len(date_list))
        width = 0.15
        i = 0
        for method in res[date_list[0]]:
            y = [res[date][method] for date in date_list]
            if method == "AC-OPT":
                # fill in blank
                ax.bar(x + width * i, y, width=width, label=method, hatch="///")
            else:
                ax.bar(x + width * i, y, width=width, label=method)
            i += 1
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(date_list)
        ax.set_xlabel("Date", fontsize=14)
        ax.set_ylabel("Average cache hit ratio", fontsize=14)
        ax.set_title(title)
        ax.legend()
        fig.savefig(self.out_path + "/avg_cache_hit_ratio_bar.pdf")
        if show:
            plt.show()


def run(input_file, output_path):
    # name = "mean_delay.pdf"
    logger.info("Reading results from %s", input_file)
    #  ========= plot mean delay line chart =========
    # input a xlsx file, read from excel to pandas dataframe
    # df = pd.read_excel(input_file, sheet_name="delay", skiprows=1, dtype="float")
    # plot_mean_delay_chart(df, "Node number", "delay(ms)", "", output_path + "/mean_delay.pdf")
    #  ========= plot bar chart =========
    # data = [9917, 8968, 4516]  # DINNRS
    # plot_bar_chart(data, "", output_path + "/DINNRS-domain-hit.pdf")
    # data = [89, 513, 4498]  # MDHT
    # plot_bar_chart(data, "", output_path + "/MDHT-level-hit.pdf")
    # ========== plot load-rate line chart =========
    # df = pd.read_excel(input_file, sheet_name="load", skiprows=1, dtype="float")
    # plot_load_rate_chart(df, "Request rate(/s)", "Average link load (KB)", "",
    #                      output_path + "/load_rate.pdf")
    # # ========== plot internal ratio chart =========
    # df = pd.read_excel(input_file, sheet_name="load", skiprows=1, dtype="float")
    # plot_internal_ratio(df, "Request rate(/s)", "Internal ratio", "",
    #                     output_path + "/internal_ratio.pdf")

    # ---------------------------paper 2-------------------------------
    # plot_cache_hit_ratio_seq_line_chart
    p2 = P2(input_file, output_path)
    p2.plot_cache_hit_ratio_seq_line_chart("Time/s", "Average cache hit ratio", "", date="0611")
    # p2.plot_avg_CHR_bar_group_chart("")


def main():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True, help="input file")
    parser.add_argument("-o", "--output", type=str, required=True, help="output path")
    args = parser.parse_args()
    run(args.input, args.output)


if __name__ == '__main__':
    main()