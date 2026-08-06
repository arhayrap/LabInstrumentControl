import csv
import uproot
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


# ------------------------------------------------------------
# User settings
# ------------------------------------------------------------

LP_BRANCHNAME = "LP2_50"

boardName = "3x3_LGAD"

MCP_Channel_num = 4
LGAD_Channel_num = 2

BIAS_VOLTAGES = np.arange(start=175, stop=200, step=1)
BIAS_VOLTAGES = [-117]


NBINS = 1000
MCP_RESOLUTION_PS = 10.0

OUTPUT_CSV = ("timeResolutionResults/"
    f"{boardName}_LP{LP_BRANCHNAME.split("_")[1]}_timing_resolution_vs_bias.csv"
)

OUTPUT_PNG = f"timeResolutionResults/{boardName}_LP{LP_BRANCHNAME.split("_")[1]}_timing_resolution_vs_bias.png"

# ------------------------------------------------------------
# Arrays for the final plot and CSV
# ------------------------------------------------------------

successful_bias_voltages = []
timing_resolutions_ps = []
timing_resolution_errors_ps = []

csv_rows = []


# ------------------------------------------------------------
# Loop over bias voltages
# ------------------------------------------------------------

for BIAS_VOLTAGE in BIAS_VOLTAGES:

    print()
    print("----------------------------------------")
    print(f"Bias voltage: {BIAS_VOLTAGE} V")
    print("----------------------------------------")

    FILEPATH = (
        f"../2_PreprocessedRoots/preprocessed_Jul28_3x3__Ch3_NEv5000_BV117000mV_MCP4500.root"
        # f"../2_PreprocessedRoots/prep_Board5/preprocessed_Board5_NEv5000_BV{abs(BIAS_VOLTAGE)}000mV_MCP4500.root"
    )


    # ------------------------------------------------------------
    # Read ROOT file
    # ------------------------------------------------------------

    with uproot.open(FILEPATH) as root_file:
        pulse = root_file["pulse"]

        arrays = pulse.arrays(
            [LP_BRANCHNAME, "amp", "t_peak", "decaytime", "risetime", "baseline", "baseline_RMS", "integral", "noise"],
            library="np"
        )


    lp = arrays[LP_BRANCHNAME]
    amp = arrays["amp"]
    t_peak = arrays["t_peak"]
    decaytime = arrays["decaytime"]
    risetime = arrays["risetime"]
    baseline = arrays["baseline"]
    baseline_RMS = arrays["baseline_RMS"]
    integral = arrays["integral"]
    noise = arrays["noise"]

    total_events = len(lp)

    print("Total events:", total_events)


    # ------------------------------------------------------------
    # Cuts
    # ------------------------------------------------------------

    cuts = {
        "LP MCP != 0": lp[:, 3] != 0.0,
        "LP LGAD != 0": lp[:, 1] != 0.0,

        # "LP MCP minimum": lp[:, 0] > -2.6,
        # "LP MCP maximum": lp[:, 0] < -2.1,

        # "LP LGAD minimum": lp[:, 1] > -2.0,
        # "LP LGAD maximum": lp[:, 1] < -0.2,

        # "Amplitude lower cut MCP": amp[:, 0] > 195,
        # "Amplitude upper cut MCP": amp[:, 0] < 600,

        # "Amplitude lower cut LGAD": amp[:, 1] > 100,
        # "Amplitude upper cut LGAD": amp[:, 1] < 450,

        # "t_peak lower cut MCP": t_peak[:, 0] > -2.3,
        # "t_peak upper cut MCP": t_peak[:, 0] < -1.5,

        # "t_peak lower cut LGAD": t_peak[:, 1] > 0.45,
        # "t_peak upper cut LGAD": t_peak[:, 1] < 0.7,

        # "decaytime lower cut MCP": decaytime[:, 0] > 100,
        # "decaytime upper cut MCP": decaytime[:, 0] < 450,

        # "decaytime lower cut LGAD": decaytime[:, 1] > 50,
        # "decaytime upper cut LGAD": decaytime[:, 1] < 200,

        # "risetime lower cut MCP": risetime[:, 0] > -3500,
        # "risetime upper cut MCP": risetime[:, 0] < -600,

        # "risetime lower cut LGAD": risetime[:, 1] > -500,
        # "risetime upper cut LGAD": risetime[:, 1] < -100,

        # "baseline lower cut MCP": baseline[:, 0] > 0,
        # "baseline upper cut MCP": baseline[:, 0] < 3,

        # "baseline lower cut LGAD": baseline[:, 1] > -2.5,
        # "baseline upper cut LGAD": baseline[:, 1] < 4,

        # "baseline_RMS lower cut MCP": baseline_RMS[:, 0] > 2.3,    
        # "baseline_RMS upper cut MCP": baseline_RMS[:, 0] < 3.5,

        # "baseline_RMS lower cut LGAD": baseline_RMS[:, 1] > 2.2,    
        # "baseline_RMS upper cut LGAD": baseline_RMS[:, 1] < 4.5,

        # "integral lower cut MCP": integral[:, 0] > None,
        # "integral upper cut MCP": integral[:, 0] < 0,

        # "integral lower cut LGAD": integral[:, 1] > None,
        # "integral upper cut LGAD": integral[:, 1] < None,
                
        # "noise lower cut MCP": noise[:, 0] < 10,
        # "noise upper cut MCP": noise[:, 0] > -15,

        # "noise lower cut LGAD": noise[:, 1] < 15,
        # "noise upper cut LGAD": noise[:, 1] > -15,
  
                        

        
    }


    # Print events passing each individual cut
    for cut_name, cut_mask in cuts.items():
        print(
            f"{cut_name:<25}: "
            f"{np.count_nonzero(cut_mask)} / {total_events}"
        )


    # Combine all cuts
    good_events = np.ones(total_events, dtype=bool)

    for cut_mask in cuts.values():
        good_events &= cut_mask


    number_good_events = np.count_nonzero(good_events)
    number_rejected_events = total_events - number_good_events

    print("Selected events:", number_good_events)
    print("Rejected events:", number_rejected_events)


    if number_good_events == 0:
        print("No events passed the cuts. Skipping this voltage.")
        continue


    # ------------------------------------------------------------
    # Calculate dt using only selected events
    # ------------------------------------------------------------

    selected_lp = lp[good_events]

    dt = selected_lp[:, 0] - selected_lp[:, 1]

    minimum_dt = np.min(dt)
    maximum_dt = np.max(dt)
    mean_dt = np.mean(dt)
    standard_deviation_dt = np.std(dt)

    print("Number of dt values:", dt.size)
    print("Minimum dt:", minimum_dt)
    print("Maximum dt:", maximum_dt)


    # ------------------------------------------------------------
    # Histogram and fit range
    # ------------------------------------------------------------

    dt_5, dt_95 = np.percentile(dt, [5, 95])

    counts, edges = np.histogram(dt, bins=NBINS)
    centers = 0.5 * (edges[:-1] + edges[1:])

    fit_bins = (
        (centers >= dt_5)
        & (centers <= dt_95)
        & (counts > 0)
    )

    fit_data = dt[
        (dt >= dt_5)
        & (dt <= dt_95)
    ]


    if np.count_nonzero(fit_bins) < 3:
        print("Not enough histogram bins for fitting.")
        continue


    # ------------------------------------------------------------
    # Gaussian fit
    # ------------------------------------------------------------

    popt, pcov = curve_fit(
        lambda x, A, mean, sigma:
            A * np.exp(-0.5 * ((x - mean) / sigma) ** 2),

        centers[fit_bins],
        counts[fit_bins],

        p0=[
            np.max(counts[fit_bins]),
            np.mean(fit_data),
            np.std(fit_data)
        ],

        maxfev=10000
    )


    A_fit, mean_fit, sigma_fit = popt

    A_error, mean_error, sigma_error = np.sqrt(
        np.diag(pcov)
    )

    sigma_fit = abs(sigma_fit)
    sigma_error = abs(sigma_error)


    # ------------------------------------------------------------
    # Timing resolution
    # ------------------------------------------------------------

    measured_resolution_ps = 1000 * sigma_fit
    measured_resolution_error_ps = 1000 * sigma_error

    resolution_squared = (
        measured_resolution_ps**2
        - MCP_RESOLUTION_PS**2
    )


    if resolution_squared <= 0:
        print("Measured resolution is smaller than MCP resolution.")
        continue


    timing_resolution_ps = np.sqrt(resolution_squared)

    timing_resolution_error_ps = (
        measured_resolution_ps
        / timing_resolution_ps
        * measured_resolution_error_ps
    )


    print(
        f"Timing resolution: "
        f"{timing_resolution_ps:.3f} "
        f"+/- {timing_resolution_error_ps:.3f} ps"
    )


    successful_bias_voltages.append(BIAS_VOLTAGE)
    timing_resolutions_ps.append(timing_resolution_ps)
    timing_resolution_errors_ps.append(
        timing_resolution_error_ps
    )


    # ------------------------------------------------------------
    # Add result to CSV
    # ------------------------------------------------------------

    csv_rows.append({
        "bias_voltage_V": BIAS_VOLTAGE,

        "timing_resolution_ps": timing_resolution_ps,
        "timing_resolution_error_ps":
            timing_resolution_error_ps,

        "measured_resolution_ps": measured_resolution_ps,
        "measured_resolution_error_ps":
            measured_resolution_error_ps,


        "total_events": total_events,
        "selected_events": number_good_events,
        "rejected_events": number_rejected_events,

        "minimum_dt_ns": minimum_dt,
        "maximum_dt_ns": maximum_dt,
        "mean_dt_ns": mean_dt,
        "standard_deviation_dt_ns": standard_deviation_dt,


        "mcp_resolution_ps": MCP_RESOLUTION_PS,


        "number_of_bins": NBINS,
        "lp_branch": LP_BRANCHNAME,
    })

# ------------------------------------------------------------
# Write CSV
# ------------------------------------------------------------

if len(csv_rows) > 0:

    with open(OUTPUT_CSV, "w", newline="") as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=csv_rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(csv_rows)

    print()
    print("CSV saved to:")
    print(OUTPUT_CSV)


# ------------------------------------------------------------
# Convert results to NumPy arrays
# ------------------------------------------------------------

successful_bias_voltages = np.array(
    successful_bias_voltages
)

timing_resolutions_ps = np.array(
    timing_resolutions_ps
)

timing_resolution_errors_ps = np.array(
    timing_resolution_errors_ps
)


# ------------------------------------------------------------
# Plot bias voltage versus timing resolution
# ------------------------------------------------------------

if len(successful_bias_voltages) > 0:

    plot_bias_voltages = successful_bias_voltages

    sorting = np.argsort(plot_bias_voltages)

    plot_bias_voltages = plot_bias_voltages[sorting]
    timing_resolutions_ps = timing_resolutions_ps[sorting]
    timing_resolution_errors_ps = (
        timing_resolution_errors_ps[sorting]
    )


    plt.figure(figsize=(8, 6))

    plt.errorbar(
        plot_bias_voltages,
        timing_resolutions_ps,
        yerr=timing_resolution_errors_ps,
        fmt="o-",
        capsize=5,
        label=f"{min(timing_resolutions_ps):.2f} ps at -{BIAS_VOLTAGES[np.where(timing_resolutions_ps == np.min(timing_resolutions_ps))]} Volts"
    )

    plt.title(f"{boardName} time resolution scan (refined, Jul24).")

    plt.xlabel("Bias voltage [V]")
    plt.ylabel("Timing resolution [ps]")

    plt.minorticks_on()
    plt.grid(which="major", alpha=0.7)
    plt.grid(which="minor", alpha=0.3)

    plt.legend()

    plt.tight_layout()

    plt.savefig(OUTPUT_PNG)
    plt.show()

else:
    print("No successful timing-resolution measurements.")
