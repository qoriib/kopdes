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
  Moon,
  Map as MapIcon
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
  latitude?: number
  longitude?: number
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
          fetch(`${API_BASE_URL}/regencies?limit=1000`).then(r => r.json()),
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

            {/* Interactive Cluster Map */}
            <Card className="shadow-none border-border">
              <CardHeader className="pb-3 flex flex-row items-center gap-2">
                <MapIcon className="w-4 h-4 text-primary" />
                <div>
                  <CardTitle className="text-sm font-bold text-foreground">Peta Sebaran Klaster Koperasi (Kabupaten/Kota)</CardTitle>
                  <p className="text-[10px] text-muted-foreground mt-0.5">Sebaran spasial wilayah kabupaten/kota di Indonesia berdasarkan kelompok klaster kinerja koperasi.</p>
                </div>
              </CardHeader>
              <CardContent className="p-0 sm:p-6 sm:pt-0">
                <ClusterMap regencies={regencies} labels={aiReport?.labels} theme={theme} />
              </CardContent>
            </Card>

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

function ClusterMap({ regencies, labels, theme }: { regencies: Regency[], labels?: Record<string, { label_name: string }>, theme: 'light' | 'dark' }) {
  const [leafletLoaded, setLeafletLoaded] = useState(false)

  useEffect(() => {
    if ((window as any).L) {
      setLeafletLoaded(true)
      return
    }

    // Load Leaflet CSS
    const link = document.createElement("link")
    link.rel = "stylesheet"
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    document.head.appendChild(link)

    // Load Leaflet JS
    const script = document.createElement("script")
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    script.async = true
    script.onload = () => {
      setLeafletLoaded(true)
    }
    document.body.appendChild(script)
  }, [])

  useEffect(() => {
    if (!leafletLoaded || regencies.length === 0) return

    const L = (window as any).L
    if (!L) return

    // Setup map
    const map = L.map("leaflet-cluster-map").setView([-2.5489, 118.0149], 5)

    // Choose map tiles based on theme
    const tileUrl = theme === 'dark'
      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'

    L.tileLayer(tileUrl, {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(map)

    // Colors corresponding to cluster labels
    const colors = ["#4f46e5", "#10b981", "#ef4444", "#f59e0b", "#3b82f6", "#8b5cf6"]

    regencies.forEach(reg => {
      if (reg.latitude && reg.longitude && reg.latitude !== 0 && reg.longitude !== 0) {
        const labelName = labels?.[reg.cluster_label.toString()]?.label_name || `Klaster ${reg.cluster_label}`
        const color = colors[reg.cluster_label % colors.length]

        const marker = L.circleMarker([reg.latitude, reg.longitude], {
          radius: 6,
          fillColor: color,
          color: "#ffffff",
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(map)

        const popupContent = `
          <div style="font-family: system-ui, sans-serif; font-size: 11px; line-height: 1.4; color: #1f2937;">
            <h4 style="margin: 0 0 2px 0; font-size: 12px; font-weight: 700; color: #111827;">${reg.regency_name}</h4>
            <span style="font-size: 9px; color: #6b7280; display: block; margin-bottom: 6px;">${reg.province_name}</span>
            <div style="margin-bottom: 6px;">
              <span style="display: inline-block; padding: 2px 6px; font-size: 9px; font-weight: bold; color: white; background-color: ${color}; border-radius: 4px;">
                ${labelName}
              </span>
            </div>
            <div style="display: grid; grid-template-columns: auto auto; gap: 2px 8px; border-top: 1px solid #e5e7eb; padding-top: 6px;">
              <span style="color: #4b5563;">Koperasi:</span><strong style="text-align: right;">${reg.jumlah_koperasi.toLocaleString()}</strong>
              <span style="color: #4b5563;">NIB:</span><strong style="text-align: right;">${reg.koperasi_nib.toLocaleString()}</strong>
              <span style="color: #4b5563;">NPWP:</span><strong style="text-align: right;">${reg.koperasi_npwp.toLocaleString()}</strong>
              <span style="color: #4b5563;">RAT:</span><strong style="text-align: right;">${reg.koperasi_rat.toLocaleString()}</strong>
              <span style="color: #4b5563; grid-column: span 2; margin-top: 4px; border-top: 1px dashed #e5e7eb; padding-top: 4px;">Nilai Transaksi:</span>
              <strong style="grid-column: span 2; text-align: left; font-size: 11px; color: #111827;">Rp ${(reg.nilai_transaksi).toLocaleString('id-ID')}</strong>
            </div>
          </div>
        `
        marker.bindPopup(popupContent)
      }
    })

    return () => {
      map.remove()
    }
  }, [leafletLoaded, regencies, labels, theme])

  if (!leafletLoaded) {
    return (
      <div className="h-[400px] w-full flex items-center justify-center bg-muted/20 border border-dashed rounded-lg">
        <div className="flex flex-col items-center gap-2">
          <div className="w-6 h-6 rounded-full border-2 border-muted border-t-primary animate-spin"></div>
          <p className="text-xs text-muted-foreground">Memuat peta interaktif...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative rounded-lg overflow-hidden border border-border shadow-sm">
      <div id="leaflet-cluster-map" className="h-[400px] w-full z-0" />
      {/* Legend inside map */}
      <div className="absolute bottom-4 left-4 bg-background/90 backdrop-blur-sm p-3 rounded-lg border border-border text-[10px] space-y-1.5 z-[1000] shadow-md max-w-[200px]">
        <h5 className="font-bold text-foreground">Legenda Klaster</h5>
        <div className="space-y-1">
          {labels && Object.keys(labels).map((key) => {
            const colors = ["#4f46e5", "#10b981", "#ef4444", "#f59e0b", "#3b82f6", "#8b5cf6"]
            const color = colors[parseInt(key) % colors.length]
            return (
              <div key={key} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                <span className="text-muted-foreground truncate" title={labels[key].label_name}>{labels[key].label_name}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
