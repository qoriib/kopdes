import { useState, useEffect } from 'react'
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
import { Theme } from '@astryxdesign/core/theme'
import { neutralTheme } from '@astryxdesign/theme-neutral/built'
import { Layout, LayoutHeader, LayoutContent, LayoutFooter, HStack, VStack } from '@astryxdesign/core/Layout'
import { Grid, GridSpan } from '@astryxdesign/core/Grid'
import { Card } from '@astryxdesign/core/Card'
import { IconButton } from '@astryxdesign/core/IconButton'
import { Badge } from '@astryxdesign/core/Badge'
import { StatusDot } from '@astryxdesign/core/StatusDot'
import { Spinner } from '@astryxdesign/core/Spinner'
import { Text, Heading } from '@astryxdesign/core/Text'
import { Divider } from '@astryxdesign/core/Divider'
import { Markdown } from '@astryxdesign/core/Markdown'

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
  const [_provinces, setProvinces] = useState<Province[]>([])
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
    <Theme theme={neutralTheme} mode={theme}>
      <Layout
        height="fill"
        header={
          <LayoutHeader hasDivider>
            <HStack justify="between" align="center" paddingInline={6} paddingBlock={3}>
              <VStack gap={0.5}>
                <Heading level={3}>SIMKOPDES</Heading>
                <Text type="supporting" color="secondary">
                  Sistem Analisis & Klasterisasi Koperasi Desa
                </Text>
              </VStack>
              <HStack align="center" gap={3}>
                <Badge
                  variant="neutral"
                  icon={<StatusDot variant="accent" isPulsing label="Live D1 Status" />}
                  label="Live D1"
                />
                <IconButton
                  variant="ghost"
                  size="sm"
                  label={theme === 'light' ? 'Beralih ke mode gelap' : 'Beralih ke mode terang'}
                  tooltip={theme === 'light' ? 'Mode Gelap' : 'Mode Terang'}
                  icon={theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
                  onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                />
              </HStack>
            </HStack>
          </LayoutHeader>
        }
        content={
          <LayoutContent padding={6}>
            {loading ? (
              <VStack align="center" justify="center" gap={3} height="60vh">
                <Spinner size="lg" label="Memuat data analisis..." />
                <Text type="supporting" color="secondary">
                  Memuat data analisis...
                </Text>
              </VStack>
            ) : (
              <VStack gap={6}>
                {/* Metric Cards Grid */}
                <Grid columns={{ minWidth: 240, max: 4 }} gap={4}>
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
                      <Card key={idx} padding={4}>
                        <VStack gap={2}>
                          <HStack justify="between" align="center">
                            <Text type="supporting" color="secondary">
                              {card.title}
                            </Text>
                            <Icon size={16} />
                          </HStack>
                          <Heading level={3}>{card.value}</Heading>
                          <Text type="supporting" color="secondary">
                            {card.sub}
                          </Text>
                        </VStack>
                      </Card>
                    )
                  })}
                </Grid>

                {/* Interactive Cluster Map Card */}
                <Card padding={5}>
                  <VStack gap={4}>
                    <HStack align="center" gap={2}>
                      <MapIcon size={18} />
                      <VStack gap={0.5}>
                        <Heading level={4}>Peta Sebaran Klaster Koperasi (Kabupaten/Kota)</Heading>
                        <Text type="supporting" color="secondary">
                          Sebaran spasial wilayah kabupaten/kota di Indonesia berdasarkan kelompok klaster kinerja koperasi.
                        </Text>
                      </VStack>
                    </HStack>
                    <ClusterMap regencies={regencies} labels={aiReport?.labels} theme={theme} />
                  </VStack>
                </Card>

                {/* Analytics Section: Executive Report & ML Performance */}
                <Grid columns={{ minWidth: 320, max: 3 }} gap={4}>
                  <GridSpan columns={2}>
                    <Card padding={5}>
                      <VStack gap={4}>
                        <HStack align="center" gap={2}>
                          <BookOpen size={18} />
                          <Heading level={4}>Laporan Analisis Eksekutif AI</Heading>
                        </HStack>
                        {aiReport?.report_text ? (
                          <Markdown
                            density="compact"
                            headingLevelStart={4}
                            autolink="gfm"
                          >
                            {aiReport.report_text.replace(/\\n/g, '\n')}
                          </Markdown>
                        ) : (
                          <Text type="body" color="secondary">
                            Laporan analisis interpretatif AI tidak ditemukan.
                          </Text>
                        )}
                      </VStack>
                    </Card>
                  </GridSpan>

                  <VStack gap={4}>
                    {/* ML Performance */}
                    <Card padding={4}>
                      <VStack gap={3}>
                        <HStack align="center" gap={2}>
                          <Award size={18} />
                          <Heading level={4}>Kinerja Model ML</Heading>
                        </HStack>
                        <VStack gap={2}>
                          <HStack justify="between" align="center">
                            <Text type="body" color="secondary">Silhouette Score</Text>
                            <Text type="body" weight="semibold">{summary?.metrics?.silhouette_score || '0.0'}</Text>
                          </HStack>
                          <Divider />
                          <HStack justify="between" align="center">
                            <Text type="body" color="secondary">Calinski-Harabasz</Text>
                            <Text type="body" weight="semibold">{summary?.metrics?.calinski_harabasz_index || '0.0'}</Text>
                          </HStack>
                          <Divider />
                          <HStack justify="between" align="center">
                            <Text type="body" color="secondary">Davies-Bouldin</Text>
                            <Text type="body" weight="semibold">{summary?.metrics?.davies_bouldin_index || '0.0'}</Text>
                          </HStack>
                          <Divider />
                          <HStack justify="between" align="center">
                            <Text type="body" color="secondary">Jumlah Klaster (K)</Text>
                            <Text type="body" weight="semibold">{summary?.metrics?.number_of_clusters || '0'}</Text>
                          </HStack>
                        </VStack>
                      </VStack>
                    </Card>

                    {/* Cluster Labels Definition */}
                    <Card padding={4}>
                      <VStack gap={3}>
                        <Heading level={4}>Definisi Klaster</Heading>
                        <VStack gap={2}>
                          {aiReport && Object.keys(aiReport.labels).map((key) => {
                            const clusterLabel = parseInt(key)
                            const item = aiReport.labels[key]
                            const badgeVariant = clusterLabel === 0 ? "blue" : clusterLabel === 1 ? "green" : clusterLabel === 2 ? "red" : clusterLabel === 3 ? "orange" : "purple"
                            return (
                              <Card key={key} padding={3}>
                                <VStack gap={1}>
                                  <HStack align="center">
                                    <Badge
                                      variant={badgeVariant as any}
                                      label={`KLASTER ${key}`}
                                    />
                                  </HStack>
                                  <Heading level={5}>{item.label_name}</Heading>
                                  <Text type="supporting" color="secondary">
                                    {item.description}
                                  </Text>
                                </VStack>
                              </Card>
                            )
                          })}
                        </VStack>
                      </VStack>
                    </Card>
                  </VStack>
                </Grid>
              </VStack>
            )}
          </LayoutContent>
        }
        footer={
          <LayoutFooter hasDivider>
            <HStack justify="center" align="center" paddingBlock={3}>
              <Text type="supporting" color="secondary">
                &copy; 2026 SIMKOPDES. Dibuat murni dengan Astryx Design System, Cloudflare Workers, Hono, dan React.
              </Text>
            </HStack>
          </LayoutFooter>
        }
      />
    </Theme>
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
      <Card padding={8}>
        <VStack gap={2} align="center" justify="center">
          <Spinner size="md" label="Memuat peta interaktif..." />
          <Text type="supporting" color="secondary">Memuat peta interaktif...</Text>
        </VStack>
      </Card>
    )
  }

  return (
    <div style={{ position: 'relative', borderRadius: 8, overflow: 'hidden', height: 400 }}>
      <div id="leaflet-cluster-map" style={{ height: '100%', width: '100%' }} />
      {/* Legend inside map */}
      <div style={{
        position: 'absolute',
        bottom: 16,
        left: 16,
        backgroundColor: theme === 'dark' ? 'rgba(20, 20, 20, 0.9)' : 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(8px)',
        padding: 12,
        borderRadius: 8,
        border: '1px solid rgba(128, 128, 128, 0.2)',
        fontSize: 11,
        zIndex: 1000,
        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
        maxWidth: 220
      }}>
        <Heading level={6}>Legenda Klaster</Heading>
        <VStack gap={1} style={{ marginTop: 6 } as any}>
          {labels && Object.keys(labels).map((key) => {
            const colors = ["#4f46e5", "#10b981", "#ef4444", "#f59e0b", "#3b82f6", "#8b5cf6"]
            const color = colors[parseInt(key) % colors.length]
            return (
              <HStack key={key} align="center" gap={1.5}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: color, display: 'inline-block', flexShrink: 0 }} />
                <Text type="supporting" color="secondary">
                  {labels[key].label_name}
                </Text>
              </HStack>
            )
          })}
        </VStack>
      </div>
    </div>
  )
}
