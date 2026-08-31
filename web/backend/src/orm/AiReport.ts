import { BaseModel } from './BaseModel';

export interface AiReportRow {
  id: number;
  report_text: string;
  labels_json: string;
  upload_date?: string;
}

export class AiReport extends BaseModel<AiReportRow> {
  constructor(db: D1Database) {
    super(db, 'ai_report');
  }

  async getLatestReport(date?: string): Promise<{ report_text: string; labels: Record<string, any> } | null> {
    let row: AiReportRow | null = null;
    if (date) {
      row = await this.findOne({ where: { upload_date: date } });
    }
    if (!row) {
      const rows = await this.find({ orderBy: 'upload_date DESC', limit: 1 });
      row = rows[0] || null;
    }
    if (!row) return null;

    let labels = {};
    if (row.labels_json) {
      try {
        labels = JSON.parse(row.labels_json);
      } catch (e) {
        console.error('Failed to parse labels_json', e);
      }
    }

    return {
      report_text: row.report_text,
      labels,
    };
  }
}
