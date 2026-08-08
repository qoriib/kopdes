export class BaseModel<T extends Record<string, any>> {
  constructor(protected db: D1Database, protected tableName: string) {}

  private buildWhereClause(where?: Record<string, any>): { sql: string; params: any[] } {
    if (!where || Object.keys(where).length === 0) {
      return { sql: '', params: [] };
    }
    const clauses: string[] = [];
    const params: any[] = [];
    for (const [key, value] of Object.entries(where)) {
      if (value === null) {
        clauses.push(`${key} IS NULL`);
      } else if (typeof value === 'object' && value.op) {
        clauses.push(`${key} ${value.op} ?`);
        params.push(value.val);
      } else {
        clauses.push(`${key} = ?`);
        params.push(value);
      }
    }
    return {
      sql: ' WHERE ' + clauses.join(' AND '),
      params,
    };
  }

  async find(options?: {
    select?: string[];
    where?: Record<string, any>;
    orderBy?: string;
    limit?: number;
    offset?: number;
  }): Promise<T[]> {
    const select = options?.select ? options.select.join(', ') : '*';
    const { sql: whereSql, params } = this.buildWhereClause(options?.where);
    
    let sql = `SELECT ${select} FROM ${this.tableName}${whereSql}`;
    
    if (options?.orderBy) {
      sql += ` ORDER BY ${options.orderBy}`;
    }
    if (options?.limit !== undefined) {
      sql += ` LIMIT ?`;
      params.push(options.limit);
    }
    if (options?.offset !== undefined) {
      sql += ` OFFSET ?`;
      params.push(options.offset);
    }

    const { results } = await this.db.prepare(sql).bind(...params).all<T>();
    return results || [];
  }

  async findOne(options?: {
    select?: string[];
    where?: Record<string, any>;
  }): Promise<T | null> {
    const select = options?.select ? options.select.join(', ') : '*';
    const { sql: whereSql, params } = this.buildWhereClause(options?.where);
    const sql = `SELECT ${select} FROM ${this.tableName}${whereSql} LIMIT 1`;
    return await this.db.prepare(sql).bind(...params).first<T>();
  }

  async count(where?: Record<string, any>): Promise<number> {
    const { sql: whereSql, params } = this.buildWhereClause(where);
    const sql = `SELECT COUNT(*) as count FROM ${this.tableName}${whereSql}`;
    const result = await this.db.prepare(sql).bind(...params).first<{ count: number }>();
    return result ? result.count : 0;
  }
}
