export interface SummaryData {
  total_provinces: number;
  total_regencies: number;
  total_koperasi: number;
  total_nib: number;
  total_npwp: number;
  total_rat: number;
  total_nilai_transaksi: number;
  metrics: {
    silhouette_score?: string;
    calinski_harabasz_index?: string;
    davies_bouldin_index?: string;
    number_of_clusters?: string;
    best_algorithm?: string;
  };
}

export interface Province {
  id: number;
  province_name: string;
  total_koperasi: number;
  koperasi_nib: number;
  koperasi_npwp: number;
  koperasi_rat: number;
  latitude?: number;
  longitude?: number;
}

export interface Regency {
  id: number;
  province_id: number;
  province_name: string;
  regency_name: string;
  total_koperasi: number;
  koperasi_nib: number;
  koperasi_npwp: number;
  koperasi_rat: number;
  nilai_transaksi: number;
  cluster_label: number;
  latitude?: number;
  longitude?: number;
}

export interface AIReport {
  report_text: string;
  labels: Record<string, { label_name: string; description: string } | string>;
}
