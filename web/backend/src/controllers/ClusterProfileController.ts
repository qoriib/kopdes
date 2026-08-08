import { Context } from 'hono';
import { Regency } from '../orm/Regency';

export class ClusterProfileController {
  static async getProfiles(c: Context) {
    try {
      const db = c.env.DB;
      const regencyModel = new Regency(db);
      const profiles = await regencyModel.getClusterProfiles();

      return c.json({ success: true, data: profiles });
    } catch (err: any) {
      return c.json({ success: false, error: err.message }, 500);
    }
  }
}
