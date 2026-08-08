import { Context } from 'hono';
import { Province } from '../orm/Province';
import { Regency } from '../orm/Regency';
import { Metric } from '../orm/Metric';

export class SummaryController {
  static async getSummary(c: Context) {
    try {
      const db = c.env.DB;
      const provinceModel = new Province(db);
      const regencyModel = new Regency(db);
      const metricModel = new Metric(db);

      const totalProv = await provinceModel.count();
      const totalReg = await regencyModel.count();
      const aggregates = await regencyModel.getAggregates();
      const metrics = await metricModel.getAllAsKeyValue();

      return c.json({
        success: true,
        data: {
          total_provinces: totalProv,
          total_regencies: totalReg,
          total_koperasi: aggregates.total_koperasi,
          total_nib: aggregates.total_nib,
          total_npwp: aggregates.total_npwp,
          total_rat: aggregates.total_rat,
          total_nilai_transaksi: aggregates.total_nilai_transaksi,
          metrics,
        },
      });
    } catch (err: any) {
      return c.json({ success: false, error: err.message }, 500);
    }
  }
}
