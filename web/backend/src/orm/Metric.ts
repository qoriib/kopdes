import { BaseModel } from './BaseModel';

export interface MetricRow {
  key: string;
  value: string;
}

export class Metric extends BaseModel<MetricRow> {
  constructor(db: D1Database) {
    super(db, 'metrics');
  }

  async getAllAsKeyValue(): Promise<Record<string, string>> {
    const rows = await this.find();
    return rows.reduce((acc, row) => {
      acc[row.key] = row.value;
      return acc;
    }, {} as Record<string, string>);
  }
}
