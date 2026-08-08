import { BaseModel } from './BaseModel';

export interface ProvinceRow {
  id: number;
  province_name: string;
  jumlah_koperasi: number;
  koperasi_nib: number;
  koperasi_npwp: number;
  koperasi_rat: number;
}

export class Province extends BaseModel<ProvinceRow> {
  constructor(db: D1Database) {
    super(db, 'provinces');
  }
}
