import { BaseModel } from './BaseModel';

export interface RegencyRow {
  id: number;
  province_id: number;
  regency_name: string;
  total_koperasi: number;
  koperasi_nib: number;
  koperasi_npwp: number;
  koperasi_rat: number;
  simpanan_pokok?: number;
  simpanan_wajib?: number;
  volume_transaksi?: number;
  nilai_transaksi: number;
  cluster_label: number;
  latitude?: number;
  longitude?: number;
  province_name?: string; // from join
  upload_date?: string;
}

export class Regency extends BaseModel<RegencyRow> {
  constructor(db: D1Database) {
    super(db, 'regencies');
  }

  async findWithProvince(options: {
    provinceId?: number;
    clusterLabel?: number;
    search?: string;
    limit: number;
    offset: number;
  }): Promise<RegencyRow[]> {
    let sql = `
      SELECT r.*, p.province_name 
      FROM regencies r 
      JOIN provinces p ON r.province_id = p.id 
      WHERE 1=1
    `;
    const params: any[] = [];

    if (options.provinceId !== undefined) {
      sql += ' AND r.province_id = ?';
      params.push(options.provinceId);
    }
    if (options.clusterLabel !== undefined) {
      sql += ' AND r.cluster_label = ?';
      params.push(options.clusterLabel);
    }
    if (options.search) {
      sql += ' AND r.regency_name LIKE ?';
      params.push(`%${options.search.toUpperCase()}%`);
    }

    sql += ' ORDER BY r.regency_name ASC LIMIT ? OFFSET ?';
    params.push(options.limit, options.offset);

    const { results } = await this.db.prepare(sql).bind(...params).all<RegencyRow>();
    return results || [];
  }

  async countWithProvince(options: {
    provinceId?: number;
    clusterLabel?: number;
    search?: string;
  }): Promise<number> {
    let sql = `
      SELECT COUNT(*) as count 
      FROM regencies r 
      JOIN provinces p ON r.province_id = p.id 
      WHERE 1=1
    `;
    const params: any[] = [];

    if (options.provinceId !== undefined) {
      sql += ' AND r.province_id = ?';
      params.push(options.provinceId);
    }
    if (options.clusterLabel !== undefined) {
      sql += ' AND r.cluster_label = ?';
      params.push(options.clusterLabel);
    }
    if (options.search) {
      sql += ' AND r.regency_name LIKE ?';
      params.push(`%${options.search.toUpperCase()}%`);
    }

    const result = await this.db.prepare(sql).bind(...params).first<{ count: number }>();
    return result ? result.count : 0;
  }

  async getAggregates(): Promise<{
    total_koperasi: number;
    total_nib: number;
    total_npwp: number;
    total_rat: number;
    total_nilai_transaksi: number;
  }> {
    const sql = `
      SELECT 
        SUM(total_koperasi) as total_koperasi,
        SUM(koperasi_nib) as total_nib,
        SUM(koperasi_npwp) as total_npwp,
        SUM(koperasi_rat) as total_rat,
        SUM(nilai_transaksi) as total_nilai_transaksi
      FROM regencies
    `;
    const result = await this.db.prepare(sql).first<any>();
    return {
      total_koperasi: result?.total_koperasi || 0,
      total_nib: result?.total_nib || 0,
      total_npwp: result?.total_npwp || 0,
      total_rat: result?.total_rat || 0,
      total_nilai_transaksi: result?.total_nilai_transaksi || 0,
    };
  }

  async getClusterProfiles(): Promise<any[]> {
    const sql = `
      SELECT 
        cluster_label,
        COUNT(*) as count,
        AVG(total_koperasi) as avg_koperasi,
        AVG(koperasi_nib) as avg_nib,
        AVG(koperasi_npwp) as avg_npwp,
        AVG(koperasi_rat) as avg_rat,
        AVG(nilai_transaksi) as avg_nilai_transaksi
      FROM regencies
      GROUP BY cluster_label
      ORDER BY cluster_label ASC
    `;
    const { results } = await this.db.prepare(sql).all<any>();
    return results || [];
  }
}
