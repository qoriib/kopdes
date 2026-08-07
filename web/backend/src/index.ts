import { Hono } from 'hono'
import { cors } from 'hono/cors'

type Env = {
  Bindings: {
    DB: D1Database
  }
}

const app = new Hono<{ Bindings: Env['Bindings'] }>()

// Enable CORS for frontend integration
app.use('/api/*', cors())

app.get('/', (c) => {
  return c.text('SIMKOPDES API Services is online!')
})

// 1. Dashboard Summary Statistics
app.get('/api/summary', async (c) => {
  try {
    const db = c.env.DB
    
    const totalProvResult = await db.prepare("SELECT COUNT(*) as count FROM provinces").first()
    const totalProv = totalProvResult ? totalProvResult.count : 0

    const totalRegResult = await db.prepare("SELECT COUNT(*) as count FROM regencies").first()
    const totalReg = totalRegResult ? totalRegResult.count : 0
    
    const statsResult = await db.prepare(`
      SELECT 
        SUM(jumlah_koperasi) as total_koperasi,
        SUM(koperasi_nib) as total_nib,
        SUM(koperasi_npwp) as total_npwp,
        SUM(koperasi_rat) as total_rat,
        SUM(nilai_transaksi) as total_nilai_transaksi
      FROM regencies
    `).first()

    const metricsRows = await db.prepare("SELECT key, value FROM metrics").all()
    const metrics = metricsRows.results.reduce((acc: Record<string, string>, row: any) => {
      acc[row.key] = row.value
      return acc;
    }, {})
    
    return c.json({
      success: true,
      data: {
        total_provinces: totalProv,
        total_regencies: totalReg,
        total_koperasi: statsResult?.total_koperasi || 0,
        total_nib: statsResult?.total_nib || 0,
        total_npwp: statsResult?.total_npwp || 0,
        total_rat: statsResult?.total_rat || 0,
        total_nilai_transaksi: statsResult?.total_nilai_transaksi || 0,
        metrics
      }
    })
  } catch (err: any) {
    return c.json({ success: false, error: err.message }, 500)
  }
})

// 2. Fetch All Provinces
app.get('/api/provinces', async (c) => {
  try {
    const db = c.env.DB
    const { results } = await db.prepare("SELECT * FROM provinces ORDER BY province_name ASC").all()
    return c.json({ success: true, data: results })
  } catch (err: any) {
    return c.json({ success: false, error: err.message }, 500)
  }
})

// 3. Fetch Paginated & Filterable Regencies
app.get('/api/regencies', async (c) => {
  try {
    const db = c.env.DB
    const provinceId = c.req.query('province_id')
    const clusterLabel = c.req.query('cluster_label')
    const search = c.req.query('search') || ''
    const page = parseInt(c.req.query('page') || '1')
    const limit = parseInt(c.req.query('limit') || '10')
    const offset = (page - 1) * limit
    
    let query = "SELECT r.*, p.province_name FROM regencies r JOIN provinces p ON r.province_id = p.id WHERE 1=1"
    let countQuery = "SELECT COUNT(*) as count FROM regencies r JOIN provinces p ON r.province_id = p.id WHERE 1=1"
    const params: any[] = []
    
    if (provinceId) {
      query += " AND r.province_id = ?"
      countQuery += " AND r.province_id = ?"
      params.push(parseInt(provinceId))
    }
    if (clusterLabel) {
      query += " AND r.cluster_label = ?"
      countQuery += " AND r.cluster_label = ?"
      params.push(parseInt(clusterLabel))
    }
    if (search) {
      query += " AND r.regency_name LIKE ?"
      countQuery += " AND r.regency_name LIKE ?"
      params.push(`%${search.toUpperCase()}%`)
    }
    
    query += " ORDER BY r.regency_name ASC LIMIT ? OFFSET ?"
    const queryParams = [...params, limit, offset]
    
    const { results } = await db.prepare(query).bind(...queryParams).all()
    const countResult = await db.prepare(countQuery).bind(...params).first()
    const totalCount = countResult ? (countResult.count as number) : 0
    
    return c.json({
      success: true,
      data: results,
      pagination: {
        page,
        limit,
        total: totalCount,
        total_pages: Math.ceil(totalCount / limit)
      }
    })
  } catch (err: any) {
    return c.json({ success: false, error: err.message }, 500)
  }
})

// 4. Fetch Cluster Profile Aggregates
app.get('/api/cluster-profiles', async (c) => {
  try {
    const db = c.env.DB
    const { results } = await db.prepare(`
      SELECT 
        cluster_label,
        COUNT(*) as count,
        AVG(jumlah_koperasi) as avg_koperasi,
        AVG(koperasi_nib) as avg_nib,
        AVG(koperasi_npwp) as avg_npwp,
        AVG(koperasi_rat) as avg_rat,
        AVG(nilai_transaksi) as avg_nilai_transaksi
      FROM regencies
      GROUP BY cluster_label
      ORDER BY cluster_label ASC
    `).all()
    return c.json({ success: true, data: results })
  } catch (err: any) {
    return c.json({ success: false, error: err.message }, 500)
  }
})

// 5. Fetch AI Interpretation report
app.get('/api/ai-report', async (c) => {
  try {
    const db = c.env.DB
    const report = await db.prepare("SELECT report_text, labels_json FROM ai_report WHERE id = 1").first()
    
    let labels = {}
    if (report?.labels_json) {
      try {
        labels = JSON.parse(report.labels_json as string)
      } catch (e) {}
    }
    
    return c.json({
      success: true,
      data: {
        report_text: report?.report_text || '',
        labels
      }
    })
  } catch (err: any) {
    return c.json({ success: false, error: err.message }, 500)
  }
})

export default app
