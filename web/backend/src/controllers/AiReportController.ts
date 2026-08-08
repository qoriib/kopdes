import { Context } from 'hono';
import { AiReport } from '../orm/AiReport';

export class AiReportController {
  static async getReport(c: Context) {
    try {
      const db = c.env.DB;
      const aiReportModel = new AiReport(db);
      const reportData = await aiReportModel.getLatestReport();

      return c.json({
        success: true,
        data: {
          report_text: reportData?.report_text || '',
          labels: reportData?.labels || {},
        },
      });
    } catch (err: any) {
      return c.json({ success: false, error: err.message }, 500);
    }
  }
}
