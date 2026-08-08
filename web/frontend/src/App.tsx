import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { 
  Building2, 
  CheckCircle,
  TrendingUp, 
  FileSpreadsheet,
  Award,
  BookOpen,
  Sun,
  Moon
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://backend.klikolio-creative.workers.dev/api'

// Interfaces
interface SummaryData {
  total_provinces: number
  total_regencies: number
  total_koperasi: number
  total_nib: number
  total_npwp: number
  total_rat: number
  total_nilai_transaksi: number
  metrics: {
    silhouette_score?: string
    calinski_harabasz_index?: string
    davies_bouldin_index?: string
    number_of_clusters?: string
  }
}

interface Province {
  id: number
  province_name: string
  jumlah_koperasi: number
  koperasi_nib: number
  koperasi_npwp: number
  koperasi_rat: number
}

interface Regency {
  id: number
  province_id: number
  province_name: string
  regency_name: string
  jumlah_koperasi: number
  koperasi_nib: number
  koperasi_npwp: number
  koperasi_rat: number
  nilai_transaksi: number
  cluster_label: number
}

interface AIReport {
  report_text: string
  labels: Record<string, { label_name: string; description: string }>
}

export default function App() {
  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [provinces, setProvinces] = useState<Province[]>([])
  const [regencies, setRegencies] = useState<Regency[]>([])
  const [aiReport, setAiReport] = useState<AIReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  // Sync theme with HTML root class list
  useEffect(() => {
    const root = window.document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [theme])

  // Fetch initial summary & datasets
  useEffect(() => {
    async function fetchInitialData() {
      try {
        setLoading(true)
        const [sumRes, provRes, regRes, aiRes] = await Promise.all([
          fetch(`${API_BASE_URL}/summary`).then(r => r.json()),
          fetch(`${API_BASE_URL}/provinces`).then(r => r.json()),
          fetch(`${API_BASE_URL}/regencies?limit=5`).then(r => r.json()),
          fetch(`${API_BASE_URL}/ai-report`).then(r => r.json())
        ])

        if (sumRes.success) setSummary(sumRes.data)
        if (provRes.success) setProvinces(provRes.data)
        if (regRes.success) setRegencies(regRes.data)
        if (aiRes.success) setAiReport(aiRes.data)
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchInitialData()
  }, [])

  // Sort and pick top 5 provinces
  const topProvinces = [...provinces]
    .sort((a, b) => b.jumlah_koperasi - a.jumlah_koperasi)
    .slice(0, 5)

  // Pick top 5 regencies by nilai transaksi
  const topRegencies = [...regencies]
    .sort((a, b) => b.nilai_transaksi - a.nilai_transaksi)
    .slice(0, 5)

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors duration-300">
      {/* Content Area */}
      <main className="flex-1 p-6 py-10 space-y-8 max-w-6xl w-full mx-auto">
        {/* Minimalist Top Bar */}
        <div className="flex items-center justify-between border-b pb-4 border-border">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground">SIMKOPDES</h1>
            <p className="text-xs text-muted-foreground">Sistem Analisis & Klasterisasi Koperasi Desa</p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-[10px] py-0.5 px-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mr-1.5 animate-pulse"></span>
              Live D1
            </Badge>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 rounded-lg"
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            >
              {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="h-[50vh] flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 rounded-full border-2 border-muted border-t-primary animate-spin"></div>
            <p className="text-muted-foreground text-xs">Memuat data analisis...</p>
          </div>
        ) : (
          <>
            {/* Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { 
                  title: 'Total Koperasi', 
                  value: summary?.total_koperasi.toLocaleString(), 
                  sub: `${summary?.total_provinces} Provinsi / ${summary?.total_regencies} Kota`, 
                  icon: Building2 
                },
                { 
                  title: 'Koperasi NIB', 
                  value: summary ? `${((summary.total_nib / summary.total_koperasi) * 100).toFixed(1)}%` : '0%', 
                  sub: `${summary?.total_nib.toLocaleString()} Bersertifikat`, 
                  icon: CheckCircle 
                },
                { 
                  title: 'Koperasi RAT', 
                  value: summary ? `${((summary.total_rat / summary.total_koperasi) * 100).toFixed(1)}%` : '0%', 
                  sub: `${summary?.total_rat.toLocaleString()} Aktif RAT`, 
                  icon: TrendingUp 
                },
                { 
                  title: 'Total Transaksi', 
                  value: summary ? `Rp ${(summary.total_nilai_transaksi / 1e12).toFixed(2)} T` : 'Rp 0', 
                  sub: 'Volume usaha teragregasi', 
                  icon: FileSpreadsheet 
                }
              ].map((card, idx) => {
                const Icon = card.icon
                return (
                  <Card key={idx} className="shadow-none border-border">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <span className="text-xs font-medium text-muted-foreground">{card.title}</span>
                      <Icon className="w-4 h-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-xl font-bold tracking-tight text-foreground">{card.value}</div>
                      <p className="text-[10px] text-muted-foreground mt-0.5">{card.sub}</p>
                    </CardContent>
                  </Card>
                )
              })}
            </div>

            {/* Visual & Analytical Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Executive Report */}
              <Card className="lg:col-span-2 shadow-none border-border">
                <CardHeader className="flex flex-row items-center gap-2 pb-3">
                  <BookOpen className="w-4 h-4 text-primary" />
                  <CardTitle className="text-sm font-bold text-foreground">Laporan Analisis Eksekutif AI</CardTitle>
                </CardHeader>
                <CardContent className="text-muted-foreground text-xs leading-relaxed font-sans">
                  {aiReport?.report_text ? (
                    <ReactMarkdown 
                      components={{
                        h1: ({node, ...props}) => <h1 className="text-sm font-bold text-foreground mt-4 mb-2 first:mt-0" {...props} />,
                        h2: ({node, ...props}) => <h2 className="text-xs font-bold text-foreground mt-3 mb-1" {...props} />,
                        p: ({node, ...props}) => <p className="mb-3 last:mb-0" {...props} />,
                        ul: ({node, ...props}) => <ul className="list-disc list-inside space-y-1 mb-3" {...props} />,
                        ol: ({node, ...props}) => <ol className="list-decimal list-inside space-y-1 mb-3" {...props} />,
                        li: ({node, ...props}) => <li className="pl-1" {...props} />,
                      }}
                    >
                      {aiReport.report_text.replace(/\\n/g, '\n')}
                    </ReactMarkdown>
                  ) : (
                    'Laporan analisis interpretatif AI tidak ditemukan.'
                  )}
                </CardContent>
              </Card>

              {/* Model Performance & Labels */}
              <div className="space-y-6">
                {/* ML Performance */}
                <Card className="shadow-none border-border">
                  <CardHeader className="flex flex-row items-center gap-2 pb-3">
                    <Award className="w-4 h-4 text-primary" />
                    <CardTitle className="text-sm font-bold text-foreground">Kinerja Model ML</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    <div className="flex justify-between items-center border-b pb-2 border-border">
                      <span className="text-muted-foreground">Silhouette Score</span>
                      <span className="font-semibold text-foreground">{summary?.metrics?.silhouette_score || '0.0'}</span>
                    </div>
                    <div className="flex justify-between items-center border-b pb-2 border-border">
                      <span className="text-muted-foreground">Calinski-Harabasz</span>
                      <span className="font-semibold text-foreground">{summary?.metrics?.calinski_harabasz_index || '0.0'}</span>
                    </div>
                    <div className="flex justify-between items-center border-b pb-2 border-border">
                      <span className="text-muted-foreground">Davies-Bouldin</span>
                      <span className="font-semibold text-foreground">{summary?.metrics?.davies_bouldin_index || '0.0'}</span>
                    </div>
                    <div className="flex justify-between items-center pb-1">
                      <span className="text-muted-foreground">Jumlah Klaster (K)</span>
                      <span className="font-semibold text-foreground">{summary?.metrics?.number_of_clusters || '0'}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Cluster Labels Definition */}
                <Card className="shadow-none border-border">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold text-foreground">Definisi Klaster</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {aiReport && Object.keys(aiReport.labels).map((key) => {
                      const clusterLabel = parseInt(key)
                      const item = aiReport.labels[key]
                      return (
                        <div key={key} className="p-3 rounded-lg border border-border bg-muted/30 space-y-1">
                          <div className="flex items-center justify-between">
                            <Badge variant={clusterLabel === 0 ? "default" : clusterLabel === 1 ? "secondary" : "outline"} className="text-[8px] py-0 px-1.5 uppercase font-bold tracking-wider">
                              Klaster {key}
                            </Badge>
                          </div>
                          <h4 className="font-bold text-xs text-foreground mt-1">{item.label_name}</h4>
                          <p className="text-[10px] text-muted-foreground leading-normal">{item.description}</p>
                        </div>
                      )
                    })}
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Top Lists Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Top Provinces */}
              <Card className="shadow-none border-border">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-bold text-foreground">Top 5 Provinsi (Populasi Koperasi)</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-[10px] font-bold uppercase tracking-wider pl-0">Provinsi</TableHead>
                        <TableHead className="text-[10px] font-bold uppercase tracking-wider text-right">Koperasi</TableHead>
                        <TableHead className="text-[10px] font-bold uppercase tracking-wider text-right pr-0">RAT</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody className="text-xs text-muted-foreground">
                      {topProvinces.map((prov, idx) => (
                        <TableRow key={prov.id || idx}>
                          <TableCell className="font-medium text-foreground pl-0">{prov.province_name}</TableCell>
                          <TableCell className="text-right">{prov.jumlah_koperasi.toLocaleString()}</TableCell>
                          <TableCell className="text-right pr-0">{prov.koperasi_rat.toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              {/* Top Regencies */}
              <Card className="shadow-none border-border">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-bold text-foreground">Top 5 Kabupaten/Kota (Transaksi Usaha)</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-[10px] font-bold uppercase tracking-wider pl-0">Kabupaten/Kota</TableHead>
                        <TableHead className="text-[10px] font-bold uppercase tracking-wider text-right">Transaksi</TableHead>
                        <TableHead className="text-[10px] font-bold uppercase tracking-wider text-right pr-0">Klaster</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody className="text-xs text-muted-foreground">
                      {topRegencies.map((reg, idx) => (
                        <TableRow key={reg.id || idx}>
                          <TableCell className="font-medium text-foreground pl-0">
                            {reg.regency_name} 
                            <span className="text-[9px] text-muted-foreground block">{reg.province_name}</span>
                          </TableCell>
                          <TableCell className="text-right font-medium text-foreground">Rp {(reg.nilai_transaksi / 1e9).toFixed(1)} M</TableCell>
                          <TableCell className="text-right pr-0">
                            <Badge variant={reg.cluster_label === 0 ? "default" : reg.cluster_label === 1 ? "secondary" : "outline"} className="text-[8px] py-0 px-1.5 font-bold">
                              {reg.cluster_label}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/20 text-muted-foreground text-center py-4 text-[10px]">
        &copy; 2026 SIMKOPDES. Dibuat dengan Cloudflare Workers, Hono, dan React.
      </footer>
    </div>
  )
}
