import { useState, useEffect } from 'react'
import { 
  LayoutDashboard, 
  Map, 
  Building2, 
  BrainCircuit, 
  Search, 
  Filter, 
  ChevronLeft, 
  ChevronRight,
  TrendingUp, 
  CheckCircle,
  FileSpreadsheet,
  Award,
  BookOpen
} from 'lucide-react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell
} from 'recharts'

const API_BASE_URL = 'http://127.0.0.1:8787/api'

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

interface ClusterProfile {
  cluster_label: number
  count: number
  avg_koperasi: number
  avg_nib: number
  avg_npwp: number
  avg_rat: number
  avg_nilai_transaksi: number
}

interface AIReport {
  report_text: string
  labels: Record<string, { label_name: string; description: string }>
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'provinces' | 'regencies' | 'ai'>('overview')
  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [provinces, setProvinces] = useState<Province[]>([])
  const [regencies, setRegencies] = useState<Regency[]>([])
  const [clusterProfiles, setClusterProfiles] = useState<ClusterProfile[]>([])
  const [aiReport, setAiReport] = useState<AIReport | null>(null)
  const [loading, setLoading] = useState(true)

  // Filters for Regencies
  const [regencySearch, setRegencySearch] = useState('')
  const [regencyProvinceFilter, setRegencyProvinceFilter] = useState('')
  const [regencyClusterFilter, setRegencyClusterFilter] = useState('')
  const [regencyPage, setRegencyPage] = useState(1)
  const [regencyPagination, setRegencyPagination] = useState({ total_pages: 1, total: 0 })

  // Filters for Provinces
  const [provinceSearch, setProvinceSearch] = useState('')

  // Fetch initial summary & datasets
  useEffect(() => {
    async function fetchInitialData() {
      try {
        setLoading(true)
        const [sumRes, provRes, profilesRes, aiRes] = await Promise.all([
          fetch(`${API_BASE_URL}/summary`).then(r => r.json()),
          fetch(`${API_BASE_URL}/provinces`).then(r => r.json()),
          fetch(`${API_BASE_URL}/cluster-profiles`).then(r => r.json()),
          fetch(`${API_BASE_URL}/ai-report`).then(r => r.json())
        ])

        if (sumRes.success) setSummary(sumRes.data)
        if (provRes.success) setProvinces(provRes.data)
        if (profilesRes.success) setClusterProfiles(profilesRes.data)
        if (aiRes.success) setAiReport(aiRes.data)
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchInitialData()
  }, [])

  // Fetch Regencies on filter/page change
  useEffect(() => {
    async function fetchRegencies() {
      try {
        const queryParams = new URLSearchParams({
          page: regencyPage.toString(),
          limit: '10',
          search: regencySearch,
          province_id: regencyProvinceFilter,
          cluster_label: regencyClusterFilter
        })
        const res = await fetch(`${API_BASE_URL}/regencies?${queryParams}`).then(r => r.json())
        if (res.success) {
          setRegencies(res.data)
          setRegencyPagination(res.pagination)
        }
      } catch (err) {
        console.error('Failed to fetch regencies:', err)
      }
    }
    fetchRegencies()
  }, [regencyPage, regencySearch, regencyProvinceFilter, regencyClusterFilter])

  // Reset pagination on filter change
  useEffect(() => {
    setRegencyPage(1)
  }, [regencySearch, regencyProvinceFilter, regencyClusterFilter])

  // Filtered provinces list
  const filteredProvinces = provinces.filter(p => 
    p.province_name.toLowerCase().includes(provinceSearch.toLowerCase())
  )

  // Chart configuration
  const clusterColors = ['#3b82f6', '#8b5cf6', '#f59e0b'] // Blue, Purple, Orange
  const chartData = clusterProfiles.map(p => ({
    name: `Klaster ${p.cluster_label}`,
    count: p.count,
    avg_transaksi: p.avg_nilai_transaksi / 1e6 // in million IDR
  }))

  return (
    <div className="min-h-screen bg-[#0f172a] text-[#e2e8f0] flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-[#334155] bg-[#1e293b]/50 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <LayoutDashboard className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              SIMKOPDES
            </h1>
            <p className="text-xs text-[#94a3b8]">Sistem Analisis & Klasterisasi Koperasi Desa</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Live Sync D1
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Sidebar */}
        <aside className="w-full lg:w-64 border-r border-[#334155] bg-[#0f172a]/80 p-4 space-y-2 flex flex-row lg:flex-col items-center lg:items-stretch overflow-x-auto lg:overflow-x-visible">
          {[
            { id: 'overview', name: 'Ringkasan', icon: LayoutDashboard },
            { id: 'provinces', name: 'Provinsi', icon: Map },
            { id: 'regencies', name: 'Kabupaten/Kota', icon: Building2 },
            { id: 'ai', name: 'Analisis AI', icon: BrainCircuit }
          ].map(tab => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                  isActive 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/15 font-semibold' 
                    : 'text-[#94a3b8] hover:text-[#f8fafc] hover:bg-[#1e293b]/40'
                }`}
              >
                <Icon className="w-5 h-5 shrink-0" />
                {tab.name}
              </button>
            )
          })}
        </aside>

        {/* Content Area */}
        <main className="flex-1 p-6 space-y-6 overflow-y-auto max-w-7xl w-full mx-auto">
          {loading ? (
            <div className="h-[60vh] flex flex-col items-center justify-center gap-3">
              <div className="w-12 h-12 rounded-full border-4 border-slate-700 border-t-blue-500 animate-spin"></div>
              <p className="text-[#94a3b8] text-sm font-medium">Memuat data analisis...</p>
            </div>
          ) : (
            <>
              {/* Tab 1: Overview */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[
                      { 
                        title: 'Total Koperasi', 
                        value: summary?.total_koperasi.toLocaleString(), 
                        sub: `${summary?.total_provinces} Provinsi / ${summary?.total_regencies} Kota`, 
                        icon: Building2, 
                        color: 'from-blue-500/20 to-indigo-500/20 text-blue-400' 
                      },
                      { 
                        title: 'Koperasi NIB', 
                        value: summary ? `${((summary.total_nib / summary.total_koperasi) * 100).toFixed(1)}%` : '0%', 
                        sub: `${summary?.total_nib.toLocaleString()} Koperasi bersertifikat`, 
                        icon: CheckCircle, 
                        color: 'from-emerald-500/20 to-teal-500/20 text-emerald-400' 
                      },
                      { 
                        title: 'Koperasi RAT', 
                        value: summary ? `${((summary.total_rat / summary.total_koperasi) * 100).toFixed(1)}%` : '0%', 
                        sub: `${summary?.total_rat.toLocaleString()} Aktif RAT (2025)`, 
                        icon: TrendingUp, 
                        color: 'from-purple-500/20 to-fuchsia-500/20 text-purple-400' 
                      },
                      { 
                        title: 'Total Transaksi', 
                        value: summary ? `Rp ${(summary.total_nilai_transaksi / 1e12).toFixed(2)} T` : 'Rp 0', 
                        sub: 'Volume usaha teragregasi', 
                        icon: FileSpreadsheet, 
                        color: 'from-amber-500/20 to-orange-500/20 text-amber-400' 
                      }
                    ].map((card, idx) => {
                      const Icon = card.icon
                      return (
                        <div key={idx} className="bg-[#1e293b]/40 border border-[#334155]/60 rounded-2xl p-5 hover:border-slate-500/30 transition-all duration-300 backdrop-blur-sm relative overflow-hidden group">
                          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-white/5 to-transparent rounded-full -mr-6 -mt-6"></div>
                          <div className="flex justify-between items-start mb-4">
                            <span className="text-sm font-semibold text-[#94a3b8]">{card.title}</span>
                            <div className={`p-2 rounded-xl bg-gradient-to-tr ${card.color}`}>
                              <Icon className="w-5 h-5" />
                            </div>
                          </div>
                          <div className="space-y-1">
                            <h3 className="text-2xl font-bold tracking-tight text-[#f8fafc]">{card.value}</h3>
                            <p className="text-xs text-[#64748b]">{card.sub}</p>
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {/* ML Performance & Cluster Overview */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Performance metrics */}
                    <div className="bg-[#1e293b]/40 border border-[#334155]/60 rounded-2xl p-6 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-4">
                          <Award className="w-5 h-5 text-indigo-400" />
                          <h3 className="font-bold text-lg text-slate-100">Kinerja Model ML</h3>
                        </div>
                        <p className="text-sm text-[#94a3b8] mb-6">
                          Hasil evaluasi model KMeans Clustering berdasarkan data transaksi dan profil legalitas SIMKOPDES.
                        </p>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center border-b border-[#334155]/40 pb-2">
                            <span className="text-sm text-[#94a3b8]">Silhouette Score</span>
                            <span className="text-sm font-bold text-indigo-300">{summary?.metrics?.silhouette_score || '0.0'}</span>
                          </div>
                          <div className="flex justify-between items-center border-b border-[#334155]/40 pb-2">
                            <span className="text-sm text-[#94a3b8]">Calinski-Harabasz Index</span>
                            <span className="text-sm font-bold text-indigo-300">{summary?.metrics?.calinski_harabasz_index || '0.0'}</span>
                          </div>
                          <div className="flex justify-between items-center border-b border-[#334155]/40 pb-2">
                            <span className="text-sm text-[#94a3b8]">Davies-Bouldin Index</span>
                            <span className="text-sm font-bold text-indigo-300">{summary?.metrics?.davies_bouldin_index || '0.0'}</span>
                          </div>
                          <div className="flex justify-between items-center pb-2">
                            <span className="text-sm text-[#94a3b8]">Jumlah Klaster (K)</span>
                            <span className="text-sm font-bold text-indigo-300">{summary?.metrics?.number_of_clusters || '0'}</span>
                          </div>
                        </div>
                      </div>
                      <div className="mt-6 p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 text-xs text-indigo-300">
                        * Nilai silhouette score optimal (~0.42) mengindikasikan klasterisasi dengan struktur pengelompokan yang solid dan representatif.
                      </div>
                    </div>

                    {/* Chart 1: Cluster Distribution */}
                    <div className="bg-[#1e293b]/40 border border-[#334155]/60 rounded-2xl p-6 lg:col-span-2">
                      <h3 className="font-bold text-lg text-slate-100 mb-4">Distribusi Keanggotaan Klaster</h3>
                      <p className="text-sm text-[#94a3b8] mb-6">
                        Jumlah Kabupaten/Kota yang masuk ke masing-masing klaster berdasarkan KMeans.
                      </p>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="name" stroke="#64748b" />
                            <YAxis stroke="#64748b" />
                            <Tooltip 
                              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', borderRadius: '12px', color: '#f8fafc' }} 
                            />
                            <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                              {chartData.map((_, index) => (
                                <Cell key={`cell-${index}`} fill={clusterColors[index % clusterColors.length]} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* Avg Transaction Chart */}
                  <div className="bg-[#1e293b]/40 border border-[#334155]/60 rounded-2xl p-6">
                    <h3 className="font-bold text-lg text-slate-100 mb-4">Rata-Rata Nilai Transaksi per Klaster (Juta Rp)</h3>
                    <p className="text-sm text-[#94a3b8] mb-6">
                      Bandingkan volume perputaran finansial dari masing-masing klaster koperasi.
                    </p>
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                          <XAxis dataKey="name" stroke="#64748b" />
                          <YAxis stroke="#64748b" />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', borderRadius: '12px', color: '#f8fafc' }}
                          />
                          <Bar dataKey="avg_transaksi" radius={[8, 8, 0, 0]}>
                            {chartData.map((_, index) => (
                              <Cell key={`cell-${index}`} fill={clusterColors[index % clusterColors.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Provinces */}
              {activeTab === 'provinces' && (
                <div className="bg-[#1e293b]/40 border border-[#334155]/60 rounded-2xl p-6 space-y-6">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                      <h2 className="text-lg font-bold text-slate-100">Kinerja Koperasi Tingkat Provinsi</h2>
                      <p className="text-xs text-[#94a3b8]">Daftar 38 provinsi di Indonesia beserta rekap data koperasinya.</p>
                    </div>
                    <div className="relative w-full sm:w-72">
                      <Search className="w-4 h-4 text-[#64748b] absolute left-3.5 top-3" />
                      <input
                        type="text"
                        placeholder="Cari provinsi..."
                        value={provinceSearch}
                        onChange={(e) => setProvinceSearch(e.target.value)}
                        className="w-full bg-[#0f172a] border border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#e2e8f0] focus:border-blue-500 focus:outline-none transition-colors"
                      />
                    </div>
                  </div>

                  <div className="overflow-x-auto rounded-xl border border-[#334155]/40">
                    <table className="w-full text-left text-sm border-collapse">
                      <thead className="bg-[#0f172a] text-[#94a3b8] font-semibold">
                        <tr>
                          <th className="p-4 border-b border-[#334155]">Nama Provinsi</th>
                          <th className="p-4 border-b border-[#334155] text-right">Jumlah Koperasi</th>
                          <th className="p-4 border-b border-[#334155] text-right">NIB</th>
                          <th className="p-4 border-b border-[#334155] text-right">NPWP</th>
                          <th className="p-4 border-b border-[#334155] text-right">RAT</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#334155]/40">
                        {filteredProvinces.map((prov) => (
                          <tr key={prov.id} className="hover:bg-[#1e293b]/20 transition-colors">
                            <td className="p-4 font-semibold text-slate-200">{prov.province_name}</td>
                            <td className="p-4 text-right">{prov.jumlah_koperasi.toLocaleString()}</td>
                            <td className="p-4 text-right">
                              <div>{prov.koperasi_nib.toLocaleString()}</div>
                              <div className="text-xs text-slate-500">{((prov.koperasi_nib / prov.jumlah_koperasi) * 100).toFixed(1)}%</div>
                            </td>
                            <td className="p-4 text-right">
                              <div>{prov.koperasi_npwp.toLocaleString()}</div>
                              <div className="text-xs text-slate-500">{((prov.koperasi_npwp / prov.jumlah_koperasi) * 100).toFixed(1)}%</div>
                            </td>
                            <td className="p-4 text-right">
                              <div>{prov.koperasi_rat.toLocaleString()}</div>
                              <div className="text-xs text-slate-500">{((prov.koperasi_rat / prov.jumlah_koperasi) * 100).toFixed(1)}%</div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Tab 3: Regencies */}
              {activeTab === 'regencies' && (
                <div className="bg-[#1e293b]/40 border border-[#334155]/60 rounded-2xl p-6 space-y-6">
                  <div className="flex justify-between items-center">
                    <div>
                      <h2 className="text-lg font-bold text-slate-100">Kumpulan Data Klaster Kabupaten/Kota</h2>
                      <p className="text-xs text-[#94a3b8]">Detail label klastering hasil KMeans dari DVC pipeline.</p>
                    </div>
                  </div>

                  {/* Filters bar */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="relative">
                      <Search className="w-4 h-4 text-[#64748b] absolute left-3.5 top-3" />
                      <input
                        type="text"
                        placeholder="Cari kabupaten/kota..."
                        value={regencySearch}
                        onChange={(e) => setRegencySearch(e.target.value)}
                        className="w-full bg-[#0f172a] border border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#e2e8f0] focus:border-blue-500 focus:outline-none transition-colors"
                      />
                    </div>

                    <div className="flex gap-2">
                      <div className="p-3 bg-[#0f172a] border border-[#334155] rounded-xl flex items-center justify-center shrink-0">
                        <Filter className="w-4 h-4 text-[#64748b]" />
                      </div>
                      <select
                        value={regencyProvinceFilter}
                        onChange={(e) => setRegencyProvinceFilter(e.target.value)}
                        className="w-full bg-[#0f172a] border border-[#334155] rounded-xl px-4 py-2 text-sm text-[#e2e8f0] focus:border-blue-500 focus:outline-none"
                      >
                        <option value="">Semua Provinsi</option>
                        {provinces.map(p => (
                          <option key={p.id} value={p.id}>{p.province_name}</option>
                        ))}
                      </select>
                    </div>

                    <select
                      value={regencyClusterFilter}
                      onChange={(e) => setRegencyClusterFilter(e.target.value)}
                      className="w-full bg-[#0f172a] border border-[#334155] rounded-xl px-4 py-2 text-sm text-[#e2e8f0] focus:border-blue-500 focus:outline-none"
                    >
                      <option value="">Semua Klaster</option>
                      <option value="0">Klaster 0</option>
                      <option value="1">Klaster 1</option>
                      <option value="2">Klaster 2</option>
                    </select>
                  </div>

                  {/* Table */}
                  <div className="overflow-x-auto rounded-xl border border-[#334155]/40">
                    <table className="w-full text-left text-sm border-collapse">
                      <thead className="bg-[#0f172a] text-[#94a3b8] font-semibold">
                        <tr>
                          <th className="p-4 border-b border-[#334155]">Nama Daerah</th>
                          <th className="p-4 border-b border-[#334155]">Provinsi</th>
                          <th className="p-4 border-b border-[#334155] text-right">Jumlah Koperasi</th>
                          <th className="p-4 border-b border-[#334155] text-right">Nilai Transaksi (Rp)</th>
                          <th className="p-4 border-b border-[#334155] text-center">Label Klaster</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#334155]/40">
                        {regencies.map((reg) => (
                          <tr key={reg.id} className="hover:bg-[#1e293b]/20 transition-colors">
                            <td className="p-4 font-semibold text-slate-200">{reg.regency_name}</td>
                            <td className="p-4 text-[#94a3b8]">{reg.province_name}</td>
                            <td className="p-4 text-right">{reg.jumlah_koperasi.toLocaleString()}</td>
                            <td className="p-4 text-right">Rp {reg.nilai_transaksi.toLocaleString()}</td>
                            <td className="p-4 text-center">
                              <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                                reg.cluster_label === 0 
                                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' 
                                  : reg.cluster_label === 1
                                  ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                              }`}>
                                Klaster {reg.cluster_label}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  <div className="flex items-center justify-between pt-4">
                    <span className="text-xs text-[#64748b]">
                      Menampilkan halaman {regencyPage} dari {regencyPagination.total_pages} ({regencyPagination.total} Kabupaten/Kota)
                    </span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setRegencyPage(p => Math.max(1, p - 1))}
                        disabled={regencyPage === 1}
                        className="p-2 border border-[#334155] hover:border-slate-500/40 rounded-lg text-[#94a3b8] hover:text-[#f8fafc] disabled:opacity-50 transition-colors"
                      >
                        <ChevronLeft className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => setRegencyPage(p => Math.min(regencyPagination.total_pages, p + 1))}
                        disabled={regencyPage === regencyPagination.total_pages}
                        className="p-2 border border-[#334155] hover:border-slate-500/40 rounded-lg text-[#94a3b8] hover:text-[#f8fafc] disabled:opacity-50 transition-colors"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: AI Analysis */}
              {activeTab === 'ai' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left panel: Executive report */}
                  <div className="lg:col-span-2 space-y-6">
                    <div className="bg-[#1e293b]/40 border border-[#334155]/60 rounded-2xl p-6">
                      <div className="flex items-center gap-2 mb-4">
                        <BookOpen className="w-5 h-5 text-indigo-400" />
                        <h3 className="font-bold text-lg text-slate-100">Laporan Analisis Eksekutif</h3>
                      </div>
                      <div className="prose prose-invert prose-sm max-w-none text-[#94a3b8] leading-relaxed space-y-4 whitespace-pre-wrap font-sans">
                        {aiReport?.report_text || 'Laporan analisis interpretatif AI tidak ditemukan.'}
                      </div>
                    </div>
                  </div>

                  {/* Right panel: Cluster definition labels */}
                  <div className="space-y-6">
                    <div className="bg-[#1e293b]/40 border border-[#334155]/60 rounded-2xl p-6">
                      <h3 className="font-bold text-lg text-slate-100 mb-4">Definisi Nama Klaster Profesional</h3>
                      <p className="text-xs text-[#94a3b8] mb-6">
                        Nama klaster representatif hasil ekstraksi interpretasi model oleh LLM.
                      </p>
                      
                      <div className="space-y-4">
                        {aiReport && Object.keys(aiReport.labels).map((key) => {
                          const clusterLabel = parseInt(key)
                          const item = aiReport.labels[key]
                          return (
                            <div key={key} className="p-4 rounded-xl bg-[#0f172a] border border-[#334155]/60 space-y-2">
                              <div className="flex items-center justify-between">
                                <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                                  clusterLabel === 0 
                                    ? 'bg-blue-500/10 text-blue-400' 
                                    : clusterLabel === 1
                                    ? 'bg-purple-500/10 text-purple-400'
                                    : 'bg-amber-500/10 text-amber-400'
                                }`}>
                                  Klaster {key}
                                </span>
                              </div>
                              <h4 className="font-bold text-sm text-slate-200">{item.label_name}</h4>
                              <p className="text-xs text-[#64748b] leading-relaxed">{item.description}</p>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-[#334155] bg-[#0f172a]/90 text-[#64748b] text-center py-4 text-xs">
        &copy; 2026 SIMKOPDES. Dibuat dengan Cloudflare Workers, Hono, dan React + Shadcn.
      </footer>
    </div>
  )
}
