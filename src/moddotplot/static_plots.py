from plotnine import (
    ggsave,
    ggplot,
    aes,
    geom_histogram,
    geom_polygon,
    scale_color_discrete,
    element_blank,
    theme,
    xlab,
    scale_fill_manual,
    scale_fill_gradientn,
    scale_color_cmap,
    coord_cartesian,
    ylab,
    scale_x_continuous,
    scale_y_continuous,
    geom_tile,
    coord_fixed,
    facet_grid,
    labs,
    element_line,
    element_text,
    theme_light,
    theme_void,
)
import pandas as pd
import numpy as np
import math
from .const import (
    DIVERGING_PALETTES,
    QUALITATIVE_PALETTES,
    SEQUENTIAL_PALETTES,
)
from typing import List
from palettable.colorbrewer import qualitative, sequential, diverging


def check_st_en_equality(df):
    unequal_rows = df[(df["q_st"] != df["r_st"]) | (df["q_en"] != df["r_en"])]
    unequal_rows.loc[:, ["q_en", "r_en", "q_st", "r_st"]] = unequal_rows[
        ["r_en", "q_en", "r_st", "q_st"]
    ].values

    df = pd.concat([df, unequal_rows], ignore_index=True)

    return df


def make_k(vals):
    return format(vals / 1e3, ",")


def make_scale(vals: list) -> str:
    scaled = [number / 1000000 for number in vals]
    return scaled


def get_colors(sdf, ncolors, is_freq, custom_breakpoints):
    assert ncolors > 2 and ncolors < 12
    bot = math.floor(min(sdf["perID_by_events"]))
    top = 100.0
    interval = (top - bot) / ncolors
    breaks = []
    if is_freq:
        breaks = np.unique(
            np.quantile(sdf["perID_by_events"], np.arange(0, 1.01, 1 / ncolors))
        )
    else:
        breaks = [bot + i * interval for i in range(ncolors + 1)]
    if custom_breakpoints:
        breaks = np.asfarray(custom_breakpoints)
    labels = np.arange(len(breaks) - 1)
    # corner case of only one %id value
    if len(breaks) == 1:
        return pd.factorize([1] * len(sdf["perID_by_events"]))[0]
    else:
        tmp = pd.cut(
            sdf["perID_by_events"], bins=breaks, labels=labels, include_lowest=True
        )
        return tmp


# TODO: Remove pandas dependency
def read_df_from_file(file_path):
    data = pd.read_csv(file_path, delimiter="\t")
    return data


def generate_diamond(row: pd.Series, side_length: float):
    x = row["w"]
    y = row["z"]
    base = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]]) * np.sqrt(2) / 2
    trans = (base * side_length) + np.array([x, y])
    df = pd.DataFrame(trans, columns=["w", "z"])
    df["discrete"] = row["discrete"]
    df["group"] = row["group"]
    return df


def read_df(
    pj,
    palette,
    palette_orientation,
    is_freq,
    custom_colors,
    custom_breakpoints,
    from_file,
):
    df = ""
    if from_file is not None:
        df = from_file
    else:
        data = pj[0]
        df = pd.DataFrame(data[1:], columns=data[0])
    hexcodes = []
    new_hexcodes = []
    if palette in DIVERGING_PALETTES:
        function_name = getattr(diverging, palette)
        hexcodes = function_name.hex_colors
        if palette_orientation == "+":
            palette_orientation = "-"
        else:
            palette_orientation = "+"
    elif palette in QUALITATIVE_PALETTES:
        function_name = getattr(qualitative, palette)
        hexcodes = function_name.hex_colors
    elif palette in SEQUENTIAL_PALETTES:
        function_name = getattr(sequential, palette)
        hexcodes = function_name.hex_colors
    else:
        function_name = getattr(sequential, "Spectral_11")
        palette_orientation = "-"
        hexcodes = function_name.hex_colors

    if palette_orientation == "-":
        new_hexcodes = hexcodes[::-1]
    else:
        new_hexcodes = hexcodes

    if custom_colors:
        new_hexcodes = custom_colors

    ncolors = len(new_hexcodes)
    # Get colors for each row based on the values in the dataframe
    df["discrete"] = get_colors(df, ncolors, is_freq, custom_breakpoints)
    # Rename columns if they have different names in the dataframe
    if "query_name" in df.columns or "#query_name" in df.columns:
        df.rename(
            columns={
                "#query_name": "q",
                "query_start": "q_st",
                "query_end": "q_en",
                "reference_name": "r",
                "reference_start": "r_st",
                "reference_end": "r_en",
            },
            inplace=True,
        )

    # Calculate the window size
    window = max(df["q_en"] - df["q_st"])

    # Calculate the position of the first and second intervals
    df["first_pos"] = df["q_st"] / window
    df["second_pos"] = df["r_st"] / window

    return df


def make_dot(sdf, title_name, palette, palette_orientation, colors):
    hexcodes = []
    new_hexcodes = []
    if palette in DIVERGING_PALETTES:
        function_name = getattr(diverging, palette)
        hexcodes = function_name.hex_colors
        if palette_orientation == "+":
            palette_orientation = "-"
        else:
            palette_orientation = "+"
    elif palette in QUALITATIVE_PALETTES:
        function_name = getattr(qualitative, palette)
        hexcodes = function_name.hex_colors
    elif palette in SEQUENTIAL_PALETTES:
        function_name = getattr(sequential, palette)
        hexcodes = function_name.hex_colors
    else:
        function_name = getattr(sequential, "Spectral_11")
        palette_orientation = "-"
        hexcodes = function_name.hex_colors

    if palette_orientation == "-":
        new_hexcodes = hexcodes[::-1]
    else:
        new_hexcodes = hexcodes
    if colors:
        new_hexcodes = colors
    max_val = max(sdf["q_en"].max(), sdf["r_en"].max())
    window = max(sdf["q_en"] - sdf["q_st"])
    print(window)
    p = (
        ggplot(sdf)
        + geom_tile(
            aes(x="q_st", y="r_st", fill="discrete", height=window, width=window)
        )
        + scale_color_discrete(guide=False)
        + scale_fill_manual(
            values=new_hexcodes,
            guide=False,
        )
        + theme(
            legend_position="none",
            panel_grid_major=element_blank(),
            panel_grid_minor=element_blank(),
            plot_background=element_blank(),
            panel_background=element_blank(),
            axis_line=element_line(color="black"),  # Adjust axis line size
            axis_text=element_text(
                family=["DejaVu Sans"]
            ),  # Change axis text font and size
            axis_ticks_major=element_line(),
            title=element_text(
                family=["DejaVu Sans"],  # Change title font family
            ),
        )
        + scale_x_continuous(labels=make_scale, limits=[0, max_val])
        + scale_y_continuous(labels=make_scale, limits=[0, max_val])
        + coord_fixed(ratio=1)
        + facet_grid("r ~ q")
        + labs(x="Genomic Position (Mbp)", y="", title=title_name)
    )

    # Adjust x-axis label size
    # p += theme(axis_title_x=element_text())

    return p


def make_tri(sdf, title_name, palette, palette_orientation, colors):
    hexcodes = []
    new_hexcodes = []
    if palette in DIVERGING_PALETTES:
        function_name = getattr(diverging, palette)
        hexcodes = function_name.hex_colors
        if palette_orientation == "+":
            palette_orientation = "-"
        else:
            palette_orientation = "+"
    elif palette in QUALITATIVE_PALETTES:
        function_name = getattr(qualitative, palette)
        hexcodes = function_name.hex_colors
    elif palette in SEQUENTIAL_PALETTES:
        function_name = getattr(sequential, palette)
        hexcodes = function_name.hex_colors
    else:
        function_name = getattr(sequential, "Spectral_11")
        palette_orientation = "-"
        hexcodes = function_name.hex_colors

    if palette_orientation == "-":
        new_hexcodes = hexcodes[::-1]
    else:
        new_hexcodes = hexcodes
    if colors:
        new_hexcodes = colors
    
    sdf["w"] = sdf["first_pos"] + sdf["second_pos"]
    sdf["z"] = -sdf["first_pos"] + sdf["second_pos"]
    sdf["group"] = range(sdf.shape[0])

    tri_scale = sdf["q_st"].max() / sdf["w"].max()
    window = max(sdf["q_en"] - sdf["q_st"]) / tri_scale

    df_d = pd.concat(generate_diamond(row[1], window) for row in sdf.iterrows()).reset_index(drop=True)
    df_d["x"] = tri_scale * df_d["w"]
    df_d["y"] = df_d["z"] * window

    plt = (
        ggplot(df_d)
        + geom_polygon(
            aes(x="x", y="y", fill="discrete", group="group")
        )
        + scale_color_discrete(guide=False)
        + scale_fill_gradientn(
            colors=new_hexcodes,
            guide=False,
        )
        + theme(
            legend_position="none",
            panel_grid_major=element_blank(),
            panel_grid_minor=element_blank(),
            plot_background=element_blank(),
            panel_background=element_blank(),
            axis_text_y=element_blank(), 
            axis_ticks_major_y=element_blank(),
            axis_line=element_line(color="black"),  # Adjust axis line size
            axis_text=element_text(
                family=["DejaVu Sans"]
            ),  # Change axis text font and size
            axis_ticks_major=element_line(),
            title=element_text(
                family=["DejaVu Sans"],  # Change title font family
            ),
        )
        + scale_x_continuous(labels=make_scale, limits=[0, None])
        + scale_y_continuous(labels=make_scale, limits=[0, None])
        + labs(x="Genomic Position (Mbp)", y="", title=title_name)
    )

    # Adjust x-axis label size
    plt += theme(axis_title_x=element_text())

    return plt


def make_hist(sdf, palette, palette_orientation, custom_colors, custom_breakpoints):
    hexcodes = []
    new_hexcodes = []
    if palette in DIVERGING_PALETTES:
        function_name = getattr(diverging, palette)
        hexcodes = function_name.hex_colors
        if palette_orientation == "+":
            palette_orientation = "-"
        else:
            palette_orientation = "+"
    elif palette in QUALITATIVE_PALETTES:
        function_name = getattr(qualitative, palette)
        hexcodes = function_name.hex_colors
    elif palette in SEQUENTIAL_PALETTES:
        function_name = getattr(sequential, palette)
        hexcodes = function_name.hex_colors
    else:
        function_name = getattr(sequential, "Spectral_11")
        palette_orientation = "-"
        hexcodes = function_name.hex_colors

    if palette_orientation == "-":
        new_hexcodes = hexcodes[::-1]
    else:
        new_hexcodes = hexcodes

    if custom_colors:
        new_hexcodes = custom_colors
    bot = np.quantile(sdf["perID_by_events"], q=0.001)
    count = sdf.shape[0]
    extra = ""

    if count > 1e6:
        extra = "\n(thousands)"

    p = (
        ggplot(data=sdf, mapping=aes(x="perID_by_events", fill="discrete"))
        + geom_histogram(bins=300)
        + scale_color_cmap(cmap_name="plasma")
        + scale_fill_manual(new_hexcodes)
        + theme_light()
        + theme(text=element_text(family=["DejaVu Sans"]))
        + theme(legend_position="none")
        + coord_cartesian(xlim=(bot, 100))
        + xlab("% Identity Estimate")
        + ylab("# of Estimates{}".format(extra))
    )
    return p


def create_plots(
    sdf,
    directory,
    name_x,
    name_y,
    palette,
    palette_orientation,
    no_hist,
    width,
    dpi,
    is_freq,
    xlim,
    custom_colors,
    custom_breakpoints,
    from_file,
    is_pairwise,
):
    # TODO: Implement xlim
    df = read_df(
        sdf,
        palette,
        palette_orientation,
        is_freq,
        custom_colors,
        custom_breakpoints,
        from_file,
    )
    sdf = df
    plot_filename = f"{directory}/{name_x}"
    if is_pairwise:
        plot_filename = f"{directory}/{name_x}_{name_y}"

    histy = make_hist(
        sdf, palette, palette_orientation, custom_colors, custom_breakpoints
    )

    if is_pairwise:
        print(width)
        heatmap = make_dot(
            sdf, plot_filename, palette, palette_orientation, custom_colors
        )
        print(f"Creating plots and saving to {plot_filename}...\n")
        ggsave(
            heatmap,
            width=9,
            height=9,
            dpi=dpi,
            format="pdf",
            filename=f"{plot_filename}.pdf",
            verbose=False,
        )
        ggsave(
            heatmap,
            width=9,
            height=9,
            dpi=dpi,
            format="png",
            filename=f"{plot_filename}.png",
            verbose=False,
        )
        if no_hist:
            print(f"{plot_filename}.pdf and {plot_filename}.png saved sucessfully. \n")
        else:
            ggsave(
                histy,
                width=3,
                height=3,
                dpi=dpi,
                format="pdf",
                filename=f"{plot_filename}_HIST.pdf",
                verbose=False,
            )
            ggsave(
                histy,
                width=3,
                height=3,
                dpi=dpi,
                format="png",
                filename=f"{plot_filename}_HIST.png",
                verbose=False,
            )
            print(
                f"{plot_filename}.pdf, {plot_filename}.png, {plot_filename}_HIST.pdf and {plot_filename}_HIST.png saved sucessfully. \n"
            )
    # Self-identity plots: Output _TRI, _FULL, and _HIST
    else:
        print(width)
        tri_plot = make_tri(
            sdf, plot_filename, palette, palette_orientation, custom_colors
        )
        full_plot = make_dot(
            check_st_en_equality(sdf),
            plot_filename,
            palette,
            palette_orientation,
            custom_colors,
        )

        print(f"Creating plots and saving to {plot_filename}...\n")
        ggsave(
            tri_plot,
            width=9,
            height=6,
            dpi=dpi,
            format="pdf",
            filename=f"{plot_filename}_TRI.pdf",
            verbose=False,
        )
        ggsave(
            tri_plot,
            width=9,
            height=6,
            dpi=dpi,
            format="png",
            filename=f"{plot_filename}_TRI.png",
            verbose=False,
        )

        ggsave(
            full_plot,
            width=9,
            height=9,
            dpi=dpi,
            format="pdf",
            filename=f"{plot_filename}_FULL.pdf",
            verbose=False,
        )
        ggsave(
            full_plot,
            width=9,
            height=9,
            dpi=dpi,
            format="png",
            filename=f"{plot_filename}_FULL.png",
            verbose=False,
        )

        if no_hist:
            print(
                f"{plot_filename}_TRI.png, {plot_filename}_TRI.pdf, {plot_filename}_FULL.png and {plot_filename}_FULL.png saved sucessfully. \n"
            )
        else:
            ggsave(
                histy,
                width=3,
                height=3,
                dpi=dpi,
                format="pdf",
                filename=plot_filename + "_HIST.pdf",
                verbose=False,
            )
            ggsave(
                histy,
                width=3,
                height=3,
                dpi=dpi,
                format="png",
                filename=plot_filename + "_HIST.png",
                verbose=False,
            )
            print(
                f"{plot_filename}_TRI.png, {plot_filename}_TRI.pdf, {plot_filename}_FULL.png, {plot_filename}_FULL.png, {plot_filename}_HIST.png and {plot_filename}_HIST.pdf, saved sucessfully. \n"
            )
