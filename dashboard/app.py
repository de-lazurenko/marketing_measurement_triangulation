import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Marketing Measurement Triangulation",
    page_icon="📊",
    layout="wide"
)

# ── Helper Functions ──────────────────────────────────────────────────────────
def adstock(series, decay):
    result = np.zeros(len(series))
    result[0] = series.iloc[0] if hasattr(series, 'iloc') else series[0]
    for t in range(1, len(series)):
        val = series.iloc[t] if hasattr(series, 'iloc') else series[t]
        result[t] = val + decay * result[t-1]
    return result

def saturation(series, alpha=2.0, gamma=0.5):
    s = pd.Series(series)
    if s.max() == 0:
        return pd.Series(np.zeros(len(s)))
    x = s / s.max()
    return x**alpha / (x**alpha + gamma**alpha)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Parameters")
st.sidebar.markdown("Adjust channel settings to see how attribution methods respond.")

st.sidebar.markdown("### True Lift (Ground Truth)")
lift_search  = st.sidebar.slider("Paid Search",  0.0, 1.0, 0.40, 0.05)
lift_social  = st.sidebar.slider("Paid Social",  0.0, 1.0, 0.25, 0.05)
lift_display = st.sidebar.slider("Display",      0.0, 1.0, 0.05, 0.05)
lift_aff     = st.sidebar.slider("Affiliate",    0.0, 1.0, 0.15, 0.05)
lift_organic = st.sidebar.slider("Organic",      0.0, 1.0, 0.10, 0.05)

st.sidebar.markdown("### Weekly Budget ($)")
budget_search  = st.sidebar.number_input("Paid Search",  value=15000, step=1000)
budget_social  = st.sidebar.number_input("Paid Social",  value=10000, step=1000)
budget_display = st.sidebar.number_input("Display",      value=5000,  step=1000)
budget_aff     = st.sidebar.number_input("Affiliate",    value=7000,  step=1000)

# ── Ground Truth Calculation ──────────────────────────────────────────────────
channels = ['paid_search', 'paid_social', 'display', 'affiliate', 'organic']

total_marketing = (
    budget_search  * lift_search  +
    budget_social  * lift_social  +
    budget_display * lift_display +
    budget_aff     * lift_aff
)

ground_truth = {
    'paid_search': round(budget_search  * lift_search  / total_marketing * 100, 2) if total_marketing > 0 else 0,
    'paid_social': round(budget_social  * lift_social  / total_marketing * 100, 2) if total_marketing > 0 else 0,
    'display':     round(budget_display * lift_display / total_marketing * 100, 2) if total_marketing > 0 else 0,
    'affiliate':   round(budget_aff     * lift_aff     / total_marketing * 100, 2) if total_marketing > 0 else 0,
    'organic':     0.0
}

# ── Navigation ────────────────────────────────────────────────────────────────
st.title("📊 Marketing Measurement Triangulation")
st.markdown("*Comparing MMM, MTA & Incrementality Testing against known ground truth*")

tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 MTA Comparison",
    "📈 MMM Analysis", 
    "🧪 Incrementality",
    "🏆 Final Benchmarking"
])

# ── Tab 1: MTA Comparison ─────────────────────────────────────────────────────
with tab1:
    st.header("Multi-Touch Attribution Comparison")
    st.markdown("Comparing all MTA methods against ground truth across 5 channels.")

    # Fixed MTA results from notebooks
    mta_data = {
        'channel':     channels,
        'Ground Truth': [ground_truth[ch] for ch in channels],
        'Last Touch':  [54.92, 25.42,  2.20,  9.47, 7.99],
        'First Touch': [34.35, 26.68, 20.60, 11.13, 7.24],
        'Linear':      [40.15, 25.15, 13.67, 11.02, 10.02],
        'Markov':      [89.55, 10.45,  0.00,  0.00, 0.00],
        'Shapley':     [38.52, 24.78, 14.34, 11.59, 10.77],
    }
    df_mta = pd.DataFrame(mta_data)

    # Chart: grouped bar
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    methods_mta = ['Ground Truth', 'Last Touch', 'First Touch', 'Linear', 'Markov', 'Shapley']
    colors_mta  = ['#000000', '#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B2']
    x = np.arange(len(channels))
    width = 0.13

    for i, (method, color) in enumerate(zip(methods_mta, colors_mta)):
        offset = (i - len(methods_mta)/2) * width + width/2
        axes[0].bar(x + offset, df_mta[method], width, label=method, color=color, alpha=0.85)

    axes[0].set_xticks(x)
    axes[0].set_xticklabels(channels, rotation=15, ha='right')
    axes[0].set_ylabel('Attribution Credit (%)')
    axes[0].set_title('Attribution by Channel and Method')
    axes[0].legend(fontsize=7)

    # Chart: bias heatmap
    bias_data = df_mta.set_index('channel').drop('Ground Truth', axis=1)
    for col in bias_data.columns:
        bias_data[col] = bias_data[col] - df_mta.set_index('channel')['Ground Truth']

    sns.heatmap(bias_data, annot=True, fmt='.1f', center=0,
                cmap='RdYlGn_r', ax=axes[1], linewidths=0.5,
                cbar_kws={'label': 'Bias (pp)'})
    axes[1].set_title('Bias vs Ground Truth\n(+ overestimate, - underestimate)')

    st.pyplot(fig)
    plt.close()

    # Key insights
    st.markdown("### Key Insights")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best MAE", "Last Touch", "4.80%")
    with col2:
        st.metric("Worst MAE", "Markov", "13.42%")
    with col3:
        st.metric("Most theoretically sound", "Shapley", "6.99% MAE")

    st.info("💡 **Display** is the hardest channel to measure — bias ranges from -2.0pp (Markov) to +18.6pp (First Touch). All MTA methods conflate channel presence with causal impact.")

    # ── Tab 2: MMM Analysis ───────────────────────────────────────────────────────
with tab2:
    st.header("Marketing Mix Modeling")
    st.markdown("Revenue decomposition using adstock and saturation transformations.")

    # Load MMM data
    try:
        df_mmm = pd.read_csv('../data/processed/df_mmm.csv', parse_dates=['week'])
    except:
        df_mmm = pd.read_csv('data/processed/df_mmm.csv', parse_dates=['week'])

    DECAY = {
        'paid_search': 0.3,
        'paid_social': 0.5,
        'display':     0.6,
        'affiliate':   0.2,
        'organic':     0.0
    }

    channel_spends = ['paid_search_spend', 'paid_social_spend',
                      'display_spend', 'affiliate_spend', 'organic_spend']

    lifts = {
        'paid_search': lift_search,
        'paid_social': lift_social,
        'display':     lift_display,
        'affiliate':   lift_aff,
        'organic':     lift_organic
    }

    # Calculate contributions
    weekly_contributions = {}
    for ch, spend_col in zip(channels, channel_spends):
        ads = adstock(df_mmm[spend_col], DECAY[ch])
        weekly_contributions[ch] = ads * lifts[ch]

    df_decomp = pd.DataFrame(weekly_contributions, index=df_mmm['week'])

    # Chart
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    colors_ch = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B2']

    # Stacked area
    bottom = np.zeros(len(df_mmm))
    for ch, color in zip(channels, colors_ch):
        axes[0].fill_between(df_mmm['week'], bottom,
                             bottom + df_decomp[ch].values,
                             label=ch, color=color, alpha=0.8)
        bottom += df_decomp[ch].values

    axes[0].set_title('Revenue Decomposition by Channel')
    axes[0].set_ylabel('Marketing Revenue ($)')
    axes[0].legend(fontsize=8)
    axes[0].tick_params(axis='x', rotation=45)

    # Attribution bar
    marketing_contrib = {ch: df_decomp[ch].mean() for ch in channels}
    total_m = sum(marketing_contrib.values())
    mmm_pct = [marketing_contrib[ch] / total_m * 100 if total_m > 0 else 0
               for ch in channels]

    x = np.arange(len(channels))
    width = 0.35
    axes[1].bar(x - width/2, [ground_truth[ch] for ch in channels],
                width, label='Ground Truth', color='black', alpha=0.7)
    axes[1].bar(x + width/2, mmm_pct,
                width, label='MMM', color=colors_ch, alpha=0.85)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(channels, rotation=15, ha='right')
    axes[1].set_ylabel('Attribution (%)')
    axes[1].set_title('MMM Attribution vs Ground Truth')
    axes[1].legend()

    st.pyplot(fig)
    plt.close()

    st.warning("⚠️ **MMM Limitation:** Ridge regression on this synthetic dataset produced unreliable coefficients due to multicollinearity — channel spends were generated with similar variance patterns. Revenue decomposition above uses known adstock parameters to demonstrate correct MMM methodology.")

    st.markdown("### Adstock Parameters")
    decay_df = pd.DataFrame({
        'Channel': channels,
        'Decay Rate': [DECAY[ch] for ch in channels],
        'Interpretation': [
            'Short effect — people search and buy quickly',
            'Medium effect — brand consideration takes time',
            'Longer effect — awareness builds slowly',
            'Short effect — direct response channel',
            'No paid spend'
        ]
    })
    st.dataframe(decay_df, hide_index=True)

    # ── Tab 3: Incrementality ─────────────────────────────────────────────────────
with tab3:
    st.header("Incrementality Testing — Geo Holdout Experiment")
    st.markdown("Difference-in-Differences analysis to estimate causal impact of paid_social.")

    # Load geo data
    try:
        df_geo = pd.read_csv('../data/processed/df_geo.csv', parse_dates=['week'])
    except:
        df_geo = pd.read_csv('data/processed/df_geo.csv', parse_dates=['week'])

    EXPERIMENT_START = pd.Timestamp('2023-07-03')

    df_geo['post'] = (df_geo['week'] >= EXPERIMENT_START).astype(int)

    pre_control  = df_geo[(df_geo['post']==0) & (df_geo['group']=='control')]['revenue'].mean()
    pre_test     = df_geo[(df_geo['post']==0) & (df_geo['group']=='test')]['revenue'].mean()
    post_control = df_geo[(df_geo['post']==1) & (df_geo['group']=='control')]['revenue'].mean()
    post_test    = df_geo[(df_geo['post']==1) & (df_geo['group']=='test')]['revenue'].mean()

    did_estimate = abs((post_control - pre_control) - (post_test - pre_test))

    # Weekly revenue by group
    df_weekly = df_geo.groupby(['week', 'group'])['revenue'].mean().reset_index()
    control_w = df_weekly[df_weekly['group'] == 'control']
    test_w    = df_weekly[df_weekly['group'] == 'test']

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Chart 1: Timeline
    axes[0].plot(control_w['week'], control_w['revenue'],
                 label='Control (paid_social OFF)', color='#C44E52', linewidth=1.5)
    axes[0].plot(test_w['week'], test_w['revenue'],
                 label='Test (business as usual)', color='#4C72B0', linewidth=1.5)
    axes[0].axvline(x=EXPERIMENT_START, color='black', linestyle='--',
                    linewidth=1.5, label='Experiment start')
    axes[0].set_title('Weekly Revenue — Control vs Test')
    axes[0].set_ylabel('Avg Revenue per Region ($)')
    axes[0].legend(fontsize=8)
    axes[0].tick_params(axis='x', rotation=45)

    # Chart 2: DiD bars
    categories = ['Pre-Period', 'Post-Period']
    x = np.arange(len(categories))
    width = 0.35
    axes[1].bar(x - width/2, [pre_control, post_control],
                width, label='Control', color='#C44E52', alpha=0.85)
    axes[1].bar(x + width/2, [pre_test, post_test],
                width, label='Test', color='#4C72B0', alpha=0.85)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(categories)
    axes[1].set_ylabel('Avg Revenue per Region ($)')
    axes[1].set_title('Difference-in-Differences')
    axes[1].legend()
    axes[1].yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, p: f'${x:,.0f}')
    )

    st.pyplot(fig)
    plt.close()

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("DiD Estimate", f"${did_estimate:,.0f}", "per region/week")
    with col2:
        st.metric("Ground Truth", "$2,500", "per region/week")
    with col3:
        st.metric("Error", "+27.9%", "vs ground truth")
    with col4:
        st.metric("P-value", "0.025", "statistically significant")

    st.success("✅ **Incrementality Testing** is the only method that estimates **causal impact** rather than correlation. DiD recovered the paid_social lift with statistical significance (p=0.025), with +27.9% error attributable to regional noise.")

    # ── Tab 4: Final Benchmarking ─────────────────────────────────────────────────
with tab4:
    st.header("Final Benchmarking — All Methods vs Ground Truth")
    st.markdown("Comprehensive comparison of all attribution methods against known incremental lift.")

    # Assemble results
    methods_all = ['last_touch', 'first_touch', 'linear', 'markov', 'shapley', 'mmm']
    method_labels = ['Last Touch', 'First Touch', 'Linear', 'Markov', 'Shapley', 'MMM']

    results = {
        'last_touch':  [54.92, 25.42,  2.20,  9.47, 7.99],
        'first_touch': [34.35, 26.68, 20.60, 11.13, 7.24],
        'linear':      [40.15, 25.15, 13.67, 11.02, 10.02],
        'markov':      [89.55, 10.45,  0.00,  0.00, 0.00],
        'shapley':     [38.52, 24.78, 14.34, 11.59, 10.77],
        'mmm':         [54.68, 32.65,  4.05,  8.61, 0.00],
    }

    gt_vals = [ground_truth[ch] for ch in channels]

    df_bench = pd.DataFrame({'channel': channels, 'ground_truth': gt_vals})
    for method, vals in results.items():
        df_bench[method] = vals

    # MAE
    mae = {m: round(np.mean(np.abs(df_bench[m] - df_bench['ground_truth'])), 2)
           for m in methods_all}

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    plt.subplots_adjust(wspace=0.4)

    # MAE bar chart
    mae_sorted = sorted(mae.items(), key=lambda x: x[1])
    labels_sorted = [method_labels[methods_all.index(m)] for m, _ in mae_sorted]
    values_sorted = [v for _, v in mae_sorted]
    colors_bar = ['#2ecc71' if v < 5 else '#f39c12' if v < 8 else '#e74c3c'
                  for v in values_sorted]

    axes[0].barh(labels_sorted, values_sorted, color=colors_bar, alpha=0.85)
    for i, v in enumerate(values_sorted):
        axes[0].text(v + 0.1, i, f'{v:.2f}%', va='center', fontsize=9)
    axes[0].axvline(x=5, color='green', linestyle='--', alpha=0.5)
    axes[0].set_xlabel('Mean Absolute Error (%)')
    axes[0].set_xlim(0, max(values_sorted) * 1.25)
    axes[0].set_title('Method Accuracy\n(Lower = Better)')

    # Bias heatmap
    bias_data = pd.DataFrame(index=channels)
    for method, label in zip(methods_all, method_labels):
        bias_data[label] = df_bench[method].values - df_bench['ground_truth'].values

    sns.heatmap(bias_data, annot=True, fmt='.1f', center=0,
                cmap='RdYlGn_r', ax=axes[1], linewidths=0.5,
                cbar_kws={'label': 'Bias (pp)'})
    axes[1].set_title('Bias vs Ground Truth\n(+ overestimate, - underestimate)')

    st.pyplot(fig)
    plt.close()

    # Summary metrics
    st.markdown("### Method Accuracy Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        best = min(mae, key=mae.get)
        st.metric("Most Accurate", method_labels[methods_all.index(best)],
                  f"MAE: {mae[best]}%")
    with col2:
        worst = max(mae, key=mae.get)
        st.metric("Least Accurate", method_labels[methods_all.index(worst)],
                  f"MAE: {mae[worst]}%")
    with col3:
        st.metric("Incrementality Error", "+27.9%",
                  "paid_social only (p=0.025)")

    # Decision framework
    st.markdown("### Decision Framework")
    framework_data = {
        'Condition': [
            'Need quick directional insight',
            'Have structured user journey data',
            'Need fair budget allocation',
            'No user-level tracking (post-iOS14)',
            'Need to prove causal impact',
            'High-stakes budget decision'
        ],
        'Recommended Method': [
            'Last Touch / First Touch',
            'Markov Chain',
            'Shapley Value',
            'MMM',
            'Incrementality Testing',
            'Triangulate all three'
        ],
        'Key Limitation': [
            'Ignores full journey',
            'Needs transition structure',
            'Computationally expensive',
            'Sensitive to multicollinearity',
            'Slow and expensive',
            'Requires all three infrastructures'
        ]
    }
    st.dataframe(pd.DataFrame(framework_data), hide_index=True, use_container_width=True)

    st.info("💡 **Key Insight:** No single method accurately measures all channels. Agreement across methods signals reliability — when Last Touch, Shapley, and MMM agree on a channel's contribution, confidence is higher.")