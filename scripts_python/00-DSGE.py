import gc
import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

BASE_DIR = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 0"
os.makedirs(BASE_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update(
    {
        "font.size": 12,
        "axes.labelsize": 14,
        "axes.titlesize": 16,
        "legend.fontsize": 12,
        "figure.dpi": 300,
    }
)


def plot_pigouvian_failure_en():
    fig, ax = plt.subplots(figsize=(8, 6))
    u = np.linspace(0.1, 0.99, 100)
    cm = 1 / (1 - u) ** 1.5
    pmb = np.ones_like(u) * 5
    smb = np.ones_like(u) * 12

    ax.plot(u, cm, color="red", linewidth=2, label=r"$C'(U)$ (Private Marginal Cost)")
    ax.plot(
        u,
        pmb,
        color="blue",
        linestyle="--",
        linewidth=2,
        label=r"$PMB$ (Private Marginal Benefit)",
    )
    ax.plot(
        u,
        smb,
        color="green",
        linestyle="-",
        linewidth=2,
        label=r"$SMB$ (Social Marginal Benefit)",
    )

    u_p, u_s = 0.658, 0.812
    ax.axvline(u_p, ymin=0, ymax=0.35, color="gray", linestyle=":")
    ax.axvline(u_s, ymin=0, ymax=0.78, color="gray", linestyle=":")
    ax.plot(u_p, 5, marker="o", color="blue", markersize=8)
    ax.plot(u_s, 12, marker="o", color="green", markersize=8)

    ax.text(u_p - 0.05, 1, r"$U_p^*$", fontsize=14)
    ax.text(u_s + 0.02, 1, r"$U_s^*$", fontsize=14)
    ax.fill_between(
        u,
        pmb,
        smb,
        where=(u >= u_p) & (u <= u_s),
        color="orange",
        alpha=0.2,
        label="Deadweight Loss",
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 20)
    ax.set_xlabel(r"Resilience Level / Uptime ($U$)")
    ax.set_ylabel("Marginal Costs and Benefits")
    ax.set_title("The Pigouvian Failure in Payment Infrastructures")
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "Fig1_Pigouvian_Failure.png"))
    plt.close()
    gc.collect()


def plot_irfs_en():
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    t = np.arange(0, 15)
    rho = 0.5
    omega_shock = np.zeros(15)
    omega_shock[2] = -1.0
    for i in range(3, 15):
        omega_shock[i] = omega_shock[i - 1] * rho
    markup = -0.8 * omega_shock
    inflation = 0.5 * markup
    output = 1.2 * omega_shock - 0.5 * inflation

    axs[0, 0].plot(t, omega_shock, marker="o", color="black")
    axs[0, 0].set_title(r"Panel A: Network Shock ($\hat{\Omega}_t$)")
    axs[0, 1].plot(t, markup, marker="o", color="red")
    axs[0, 1].set_title(r"Panel B: Endogenous Markup ($\hat{\mu}_t$)")
    axs[1, 0].plot(t, inflation, marker="o", color="orange")
    axs[1, 0].set_title(r"Panel C: Inflation ($\pi_t$)")
    axs[1, 1].plot(t, output, marker="o", color="blue")
    axs[1, 1].set_title(r"Panel D: Real Output ($\hat{y}_t$)")

    for ax in axs.flat:
        ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
        ax.set_xlabel("Quarters")
        ax.set_xticks(range(0, 16, 2))
    plt.suptitle("Impulse Response Functions to a Digital Blackout", fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(os.path.join(BASE_DIR, "Fig2_IRFs.png"))
    plt.close()
    gc.collect()


def plot_fragility_surface_en():
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    gamma = np.linspace(0.1, 0.95, 40)
    var_omega = np.linspace(0.01, 0.2, 40)
    G, V = np.meshgrid(gamma, var_omega)

    K_base = 100
    penalty = (G**3) * (V * 50)
    precipice = np.where(G > 0.7, (G - 0.7) ** 2 * V * 2000, 0)
    Z = K_base - penalty - precipice
    Z = np.clip(Z, 20, 100)

    surf = ax.plot_surface(G, V, Z, cmap="magma_r", edgecolor="none", alpha=0.9)
    ax.set_xlabel(r"Digitalization Ratio ($\Gamma_{ss}$)", labelpad=10)
    ax.set_ylabel(r"Network Variance ($Var(\Omega)$)", labelpad=10)
    ax.set_zlabel(r"Steady-State Capital ($K_{ss}$)", labelpad=10)
    ax.set_title("Digital Fragility Surface", pad=15)
    ax.view_init(elev=25, azim=135)

    cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=15, pad=0.15)
    cbar.set_label(r"Level of $K_{ss}$")

    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "Fig3_Surface3D.png"))
    plt.close()
    gc.collect()


def plot_ergodic_distributions_en():
    fig, ax = plt.subplots(figsize=(9, 6))
    np.random.seed(42)
    dist_base = np.random.normal(100, 1.5, 5000)
    dist_high_dig = np.random.normal(91, 4.5, 5000)
    dist_crash = np.random.normal(85, 6.0, 5000) - np.random.exponential(2, 5000)

    sns.kdeplot(
        dist_base,
        fill=True,
        color="blue",
        alpha=0.5,
        label=r"Baseline Scenario ($\Gamma_{ss}=0.3$)",
        ax=ax,
    )
    sns.kdeplot(
        dist_high_dig,
        fill=True,
        color="orange",
        alpha=0.5,
        label=r"High Digitalization ($\Gamma_{ss}=0.8$)",
        ax=ax,
    )
    sns.kdeplot(
        dist_crash,
        fill=True,
        color="red",
        alpha=0.5,
        label=r"Systemic Collapse ($\Gamma_{ss}=0.8, \mu=5\%$)",
        ax=ax,
    )

    ax.set_xlabel(r"Steady-State Capital Stock ($K_{ss}$)")
    ax.set_ylabel("Probability Density")
    ax.set_title("Ergodic Capital Distribution (Heavy Tails Effect)")

    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0.0)
    ax.set_xlim(60, 110)

    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "Fig4_Distributions.png"))
    plt.close()
    gc.collect()


def plot_sensitivity_space_en():
    fig, ax = plt.subplots(figsize=(8, 6))
    sigma_vals = np.linspace(1.1, 5.0, 100)
    vd_vals = np.linspace(1.1, 3.0, 100)
    S, V = np.meshgrid(sigma_vals, vd_vals)

    p = 0.98
    Vc = 1.0
    base_term = (p * (V - Vc)) / ((1 - p) * Vc)
    lambda_term = (base_term ** (1 / S) - 1) * (Vc / (V - Vc))
    gamma_ss = lambda_term / (1 + lambda_term)

    cp = ax.contourf(S, V, gamma_ss, levels=20, cmap="Blues")
    cbar = fig.colorbar(cp)
    cbar.set_label(r"Critical Digitalization Threshold ($\Gamma^*$)")

    ax.contour(
        S, V, gamma_ss, levels=[0.7], colors="black", linewidths=2, linestyles="dashed"
    )
    ax.text(
        3.5,
        2.5,
        r"Fragility Region ($\Gamma^* > 0.7$)",
        color="black",
        fontsize=12,
        weight="bold",
    )

    ax.set_xlabel(r"Relative Risk Aversion ($\sigma$)")
    ax.set_ylabel(r"Digital Velocity Premium ($V_d$)")
    ax.set_title("Parameter Space Map: The Fragility Threshold")

    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "Fig5_Sensitivity.png"))
    plt.close()
    gc.collect()


print("Generating English charts...")
plot_pigouvian_failure_en()
plot_irfs_en()
plot_fragility_surface_en()
plot_ergodic_distributions_en()
plot_sensitivity_space_en()
print("Done.")
