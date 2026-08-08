import { Context } from 'hono';
import { Province } from '../orm/Province';

export class ProvinceController {
  static async getAll(c: Context) {
    try {
      const db = c.env.DB;
      const provinceModel = new Province(db);
      const provinces = await provinceModel.find({ orderBy: 'province_name ASC' });

      return c.json({ success: true, data: provinces });
    } catch (err: any) {
      return c.json({ success: false, error: err.message }, 500);
    }
  }
}
