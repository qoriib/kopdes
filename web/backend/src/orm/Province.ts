import { BaseModel } from './BaseModel';

export interface ProvinceRow {
  id: number;
  province_name: string;
  total_koperasi: number;
  koperasi_nib: number;
  koperasi_npwp: number;
  koperasi_rat: number;
  simpanan_pokok?: number;
  simpanan_wajib?: number;
  volume_transaksi?: number;
  nilai_transaksi?: number;
  latitude?: number;
  longitude?: number;
  upload_date?: string;
}

export class Province extends BaseModel<ProvinceRow> {
  constructor(db: D1Database) {
    super(db, 'provinces');
  }
}
