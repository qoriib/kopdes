import pandas as pd
from config import PROMPT_MD


# FUNGSI MENGHITUNG STATISTIK DESKRIPTIF KLASTER
def compute_cluster_descriptive_stats(regencies_df: pd.DataFrame, selected_features: list) -> pd.DataFrame:
    active_features = []
    for feature in selected_features:
        if feature in regencies_df.columns:
            active_features.append(feature)

    grouped_data = regencies_df.groupby("cluster_label")[active_features]
    stats_df = grouped_data.agg(["mean", "std", "median", "min", "max"]).round(2)
    return stats_df


# FUNGSI MEMFORMAT STATISTIK DESKRIPTIF KE MARKDOWN
def format_descriptive_stats_markdown(stats_df: pd.DataFrame, regencies_df: pd.DataFrame) -> str:
    markdown_lines = []
    cluster_counts = regencies_df["cluster_label"].value_counts().to_dict()

    for cluster_label in sorted(stats_df.index):
        count = cluster_counts.get(cluster_label, 0)
        markdown_lines.append(f"\n### Statistik Klaster {cluster_label} ({count} Kabupaten/Kota)")

        feature_names = stats_df.columns.levels[0]
        for feature in feature_names:
            mean_val = stats_df.loc[cluster_label, (feature, "mean")]
            std_val = stats_df.loc[cluster_label, (feature, "std")]
            median_val = stats_df.loc[cluster_label, (feature, "median")]
            min_val = stats_df.loc[cluster_label, (feature, "min")]
            max_val = stats_df.loc[cluster_label, (feature, "max")]

            label_text = feature.replace("_", " ").title()
            if "nilai" in feature or "simpanan" in feature:
                markdown_lines.append(
                    f"- **{label_text}**: Rata-rata = Rp {mean_val:,.2f} (Median = Rp {median_val:,.2f}, Std = Rp {std_val:,.2f}, Min = Rp {min_val:,.2f}, Max = Rp {max_val:,.2f})"
                )
            elif "rasio" in feature:
                markdown_lines.append(
                    f"- **{label_text}**: Rata-rata = {mean_val:.2f}% (Median = {median_val:.2f}%, Min = {min_val:.2f}%, Max = {max_val:.2f}%)"
                )
            else:
                markdown_lines.append(
                    f"- **{label_text}**: Rata-rata = {mean_val:,.2f} (Median = {median_val:,.2f}, Std = {std_val:,.2f}, Min = {min_val:,.2f}, Max = {max_val:,.2f})"
                )

    return "\n".join(markdown_lines)


# FUNGSI MEMBENTUK LAPORAN DAN TIPOLOGI KLASTER
def generate_cluster_typology(regencies_df: pd.DataFrame, selected_features: list) -> tuple[dict, str, pd.DataFrame]:
    stats_df = compute_cluster_descriptive_stats(regencies_df, selected_features)
    stats_markdown = format_descriptive_stats_markdown(stats_df, regencies_df)

    active_features = []
    for feature in selected_features:
        if feature in regencies_df.columns:
            active_features.append(feature)

    cluster_profiles_df = regencies_df.groupby("cluster_label")[active_features].mean().round(2)

    cluster_sections = []
    cluster_labels_map = {}
    total_regencies = len(regencies_df)

    for cluster_label, group_data in regencies_df.groupby("cluster_label"):
        count = len(group_data)
        percentage = round((count / total_regencies) * 100, 1)

        cluster_name = f"Klaster {cluster_label}"
        cluster_labels_map[str(cluster_label)] = f"{cluster_name} ({count} Kab/Kota - {percentage}%)"

        section_text = f"### {cluster_name} ({count} Kabupaten/Kota — {percentage}% dari Total Nasional)\n"
        section_text += "**Profil Statistik Indikator Koperasi:**\n"
        for feature in active_features:
            mean_val = group_data[feature].mean()
            median_val = group_data[feature].median()
            feature_title = feature.replace("_", " ").title()

            if "nilai" in feature or "simpanan" in feature:
                section_text += f"- {feature_title}: Rata-rata = Rp {mean_val:,.2f} (Median: Rp {median_val:,.2f})\n"
            elif "rasio" in feature:
                section_text += f"- {feature_title}: Rata-rata = {mean_val:.2f}% (Median: {median_val:.2f}%)\n"
            else:
                section_text += f"- {feature_title}: Rata-rata = {mean_val:,.2f} (Median: {median_val:,.2f})\n"

        cluster_sections.append(section_text)

    prompt_template_file = open(PROMPT_MD, "r", encoding="utf-8")
    prompt_template = prompt_template_file.read()

    complete_report_markdown = prompt_template.format(
        cluster_descriptive_stats=stats_markdown,
        total_regencies=total_regencies,
        cluster_sections="\n\n".join(cluster_sections),
    )

    return cluster_labels_map, complete_report_markdown, cluster_profiles_df
