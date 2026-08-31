import type { SummaryData, Province, Regency, AIReport } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://backend.klikolio-creative.workers.dev/api';

export async function fetchSummary(): Promise<SummaryData> {
  const res = await fetch(`${API_BASE_URL}/summary`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error || 'Gagal memuat ringkasan data');
  return json.data;
}

export async function fetchProvinces(): Promise<Province[]> {
  const res = await fetch(`${API_BASE_URL}/provinces`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error || 'Gagal memuat data provinsi');
  return json.data;
}

export async function fetchRegencies(limit = 1000): Promise<Regency[]> {
  const res = await fetch(`${API_BASE_URL}/regencies?limit=${limit}`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error || 'Gagal memuat data kabupaten/kota');
  return json.data;
}

export async function fetchAIReport(): Promise<AIReport> {
  const res = await fetch(`${API_BASE_URL}/ai-report`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error || 'Gagal memuat laporan AI');
  return json.data;
}
