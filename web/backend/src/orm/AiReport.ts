import { BaseModel } from './BaseModel';

export interface AiReportRow {
  id: number;
  report_text: string;
  labels_json: string;
}

export class AiReport extends BaseModel<AiReportRow> {
  constructor(db: D1Database) {
    super(db, 'ai_report');
  }

  async getLatestReport(): Promise<{ report_text: string; labels: Record<string, any> } | null> {
    const row = await this.findOne({ where: { id: 1 } });
    if (!row) return null;

    let labels = {};
    if (row.labels_json) {
      try {
        labels = JSON.parse(row.labels_json);
      } catch (e) {}
    }

    return {
      report_text: row.report_text,
      labels,
    };
  }
}
