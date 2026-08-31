import { useMemo } from 'react';
import { Card } from '@astryxdesign/core/Card';
import { HStack } from '@astryxdesign/core/Layout';
import { Toolbar } from '@astryxdesign/core/Toolbar';
import { Text } from '@astryxdesign/core/Text';
import { Button } from '@astryxdesign/core/Button';
import { TextInput } from '@astryxdesign/core/TextInput';
import { Selector } from '@astryxdesign/core/Selector';
import { Pagination } from '@astryxdesign/core/Pagination';
import { Divider } from '@astryxdesign/core/Divider';
import { StatusDot, type StatusDotVariant } from '@astryxdesign/core/StatusDot';
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl';
import {
  Table,
  proportional,
  useTableSortable,
  useTableSortableState,
  useTableRowIndex,
  type TableColumn,
} from '@astryxdesign/core/Table';
import { Search, RotateCcw, MapPin, Building2 } from 'lucide-react';
import type { Province, Regency, AIReport } from '@/types';

interface DataTableSectionProps {
  provinces: Province[];
  regencies: Regency[];
  aiReport: AIReport | null;
  searchParams?: {
    type: 'regencies' | 'provinces';
    search: string;
    cluster: string;
    date?: string;
    page: number;
  };
  onUpdateSearch?: (
    updates: Partial<{
      type: 'regencies' | 'provinces';
      search: string;
      cluster: string;
      date: string;
      page: number;
    }>
  ) => void;
}

type TableRowData = Record<string, unknown>;

const CLUSTER_STATUS_VARIANTS: StatusDotVariant[] = [
  'accent',
  'success',
  'error',
  'warning',
  'neutral',
];

export function DataTableSection({
  provinces,
  regencies,
  aiReport,
  searchParams = { type: 'regencies', search: '', cluster: 'all', date: '', page: 1 },
  onUpdateSearch,
}: DataTableSectionProps) {
  const activeDataType = searchParams.type;
  const searchQuery = searchParams.search;
  const selectedCluster = searchParams.cluster;
  const currentPage = searchParams.page;
  const rowsPerPage = 12;

  const updateField = (field: string, val: unknown) => {
    if (onUpdateSearch) {
      onUpdateSearch({ [field]: val });
    }
  };

  // Opsi tanggal snapshot tunggal
  const availableDates = useMemo(() => {
    const dates = new Set<string>();
    regencies.forEach((r) => {
      const uploadDate = (r as unknown as { upload_date?: string }).upload_date;
      if (uploadDate) {
        dates.add(uploadDate);
      }
    });
    provinces.forEach((p) => {
      const uploadDate = (p as unknown as { upload_date?: string }).upload_date;
      if (uploadDate) {
        dates.add(uploadDate);
      }
    });
    const arr = Array.from(dates).sort().reverse();
    return arr.length > 0 ? arr : ['2026-08-31'];
  }, [regencies, provinces]);

  // Snapshot aktif terpilih
  const activeSnapshotDate = useMemo(() => {
    if (searchParams.date && availableDates.includes(searchParams.date)) {
      return searchParams.date;
    }
    return availableDates[0];
  }, [searchParams.date, availableDates]);

  // Opsi dropdown snapshot
  const dateOptions = useMemo(() => {
    return availableDates.map((d) => ({
      value: d,
      label: `Snapshot ${d}`,
    }));
  }, [availableDates]);

  // Opsi filter klaster untuk Kabupaten/Kota
  const clusterOptions = useMemo(() => {
    const opts = [{ value: 'all', label: 'Semua Klaster' }];
    if (aiReport?.labels) {
      Object.keys(aiReport.labels).forEach((key) => {
        opts.push({ value: key, label: `Klaster ${key}` });
      });
    }
    return opts;
  }, [aiReport]);

  // Filter dataset kabupaten/kota
  const filteredRegencies = useMemo(() => {
    return regencies.filter((item) => {
      const matchSearch =
        !searchQuery ||
        (item.regency_name || '')
          .toLowerCase()
          .includes(searchQuery.toLowerCase()) ||
        (item.province_name || '')
          .toLowerCase()
          .includes(searchQuery.toLowerCase());

      const matchCluster =
        selectedCluster === 'all' ||
        item.cluster_label.toString() === selectedCluster;

      const uploadDate =
        (item as unknown as { upload_date?: string }).upload_date || availableDates[0];
      const matchDate = uploadDate === activeSnapshotDate;

      return matchSearch && matchCluster && matchDate;
    });
  }, [regencies, searchQuery, selectedCluster, activeSnapshotDate, availableDates]);

  // Filter dataset provinsi
  const filteredProvinces = useMemo(() => {
    return provinces.filter((item) => {
      const matchSearch =
        !searchQuery ||
        (item.province_name || '')
          .toLowerCase()
          .includes(searchQuery.toLowerCase());

      const uploadDate =
        (item as unknown as { upload_date?: string }).upload_date || availableDates[0];
      const matchDate = uploadDate === activeSnapshotDate;

      return matchSearch && matchDate;
    });
  }, [provinces, searchQuery, activeSnapshotDate, availableDates]);

  const activeDataset: TableRowData[] = (
    activeDataType === 'regencies' ? filteredRegencies : filteredProvinces
  ) as unknown as TableRowData[];

  const totalItems = activeDataset.length;
  const totalPages = Math.ceil(totalItems / rowsPerPage) || 1;

  // Sorting state dengan Astryx useTableSortableState
  const { sortedData, sortConfig } = useTableSortableState<TableRowData>({
    data: activeDataset,
    defaultSort: [],
  });

  // Paginated Data
  const paginatedData = useMemo(() => {
    return sortedData.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);
  }, [sortedData, currentPage, rowsPerPage]);

  const sortPlugin = useTableSortable(sortConfig);
  const rowIndexPlugin = useTableRowIndex({
    data: paginatedData,
    startFrom: (currentPage - 1) * rowsPerPage + 1,
  });

  const handleTabChange = (type: string) => {
    if (onUpdateSearch) {
      onUpdateSearch({
        type: type as 'regencies' | 'provinces',
        page: 1,
        cluster: 'all',
      });
    }
  };

  const handleResetFilters = () => {
    if (onUpdateSearch) {
      onUpdateSearch({
        search: '',
        cluster: 'all',
        page: 1,
      });
    }
  };

  const hasActiveFilters = searchQuery !== '' || selectedCluster !== 'all';

  // Kolom Tabel Kabupaten/Kota
  const regencyColumns: TableColumn<TableRowData>[] = [
    {
      key: 'regency_name',
      header: 'Kabupaten / Kota',
      width: proportional(2.2),
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body" weight="semibold">
          {String(row.regency_name || '-')}
        </Text>
      ),
    },
    {
      key: 'province_name',
      header: 'Provinsi',
      width: proportional(1.8),
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body" color="secondary">
          {String(row.province_name || '-')}
        </Text>
      ),
    },
    {
      key: 'cluster_label',
      header: 'Klaster',
      width: proportional(1.4),
      sortable: true,
      renderCell: (row: TableRowData) => {
        const clusterNum = Number(row.cluster_label ?? 0);
        const variant =
          CLUSTER_STATUS_VARIANTS[clusterNum % CLUSTER_STATUS_VARIANTS.length];

        return (
          <HStack align="center" gap={1.5}>
            <StatusDot variant={variant} label={`Klaster ${clusterNum}`} />
            <Text type="body" weight="medium">
              Klaster {clusterNum}
            </Text>
          </HStack>
        );
      },
    },
    {
      key: 'total_koperasi',
      header: 'Total Koperasi',
      width: proportional(1.2),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body" weight="medium">
          {Number(row.total_koperasi || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
    {
      key: 'koperasi_nib',
      header: 'NIB',
      width: proportional(1),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body">
          {Number(row.koperasi_nib || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
    {
      key: 'koperasi_npwp',
      header: 'NPWP',
      width: proportional(1),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body">
          {Number(row.koperasi_npwp || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
    {
      key: 'koperasi_rat',
      header: 'RAT',
      width: proportional(1),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body">
          {Number(row.koperasi_rat || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
    {
      key: 'nilai_transaksi',
      header: 'Nilai Transaksi',
      width: proportional(2),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body" weight="semibold">
          Rp {Number(row.nilai_transaksi || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
  ];

  // Kolom Tabel Provinsi
  const provinceColumns: TableColumn<TableRowData>[] = [
    {
      key: 'province_name',
      header: 'Nama Provinsi',
      width: proportional(3.5),
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body" weight="semibold">
          {String(row.province_name || '-')}
        </Text>
      ),
    },
    {
      key: 'total_koperasi',
      header: 'Total Koperasi',
      width: proportional(1.8),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body" weight="medium">
          {Number(row.total_koperasi || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
    {
      key: 'koperasi_nib',
      header: 'Koperasi NIB',
      width: proportional(1.5),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body">
          {Number(row.koperasi_nib || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
    {
      key: 'koperasi_npwp',
      header: 'Koperasi NPWP',
      width: proportional(1.5),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body">
          {Number(row.koperasi_npwp || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
    {
      key: 'koperasi_rat',
      header: 'Koperasi RAT Aktif',
      width: proportional(1.5),
      align: 'end',
      sortable: true,
      renderCell: (row: TableRowData) => (
        <Text type="body">
          {Number(row.koperasi_rat || 0).toLocaleString('id-ID')}
        </Text>
      ),
    },
  ];

  return (
    <Card padding={0}>
      {/* Toolbar Terintegrasi untuk Form & Filter */}
      <Toolbar
        label="Filter Tabel Data"
        size="sm"
        startContent={
          <HStack align="center" gap={3} wrap="wrap">
            <SegmentedControl
              label="Tipe Data"
              value={activeDataType}
              onChange={handleTabChange}
              size="sm"
            >
              <SegmentedControlItem
                value="regencies"
                label="Kabupaten / Kota"
                icon={<MapPin size={14} />}
              />
              <SegmentedControlItem
                value="provinces"
                label="Provinsi"
                icon={<Building2 size={14} />}
              />
            </SegmentedControl>

            <TextInput
              label="Pencarian"
              isLabelHidden
              startIcon={<Search size={15} />}
              placeholder="Cari wilayah..."
              value={searchQuery}
              onChange={(val) => updateField('search', val)}
              size="sm"
              width={220}
            />
          </HStack>
        }
        endContent={
          <HStack align="center" gap={2} wrap="wrap">
            {activeDataType === 'regencies' && (
              <Selector
                label="Klaster"
                isLabelHidden
                placeholder="Semua Klaster"
                value={selectedCluster}
                onChange={(val) => updateField('cluster', val)}
                options={clusterOptions}
                size="sm"
                width={180}
              />
            )}

            <Selector
              label="Snapshot"
              isLabelHidden
              value={activeSnapshotDate}
              onChange={(val) => updateField('date', val)}
              options={dateOptions}
              size="sm"
              width={170}
            />

            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                label="Reset"
                icon={<RotateCcw size={14} />}
                onClick={handleResetFilters}
              />
            )}
          </HStack>
        }
      />

      <Divider />

      {/* Tabel Data Astryx */}
      <Table
        data={paginatedData}
        columns={activeDataType === 'regencies' ? regencyColumns : provinceColumns}
        plugins={{
          sort: sortPlugin,
          rowIndex: rowIndexPlugin,
        }}
        density="balanced"
        dividers="rows"
        hasHover
      />

      <Divider />

      {/* Footer Paginasi & Total Entri */}
      <HStack
        justify="between"
        align="center"
        paddingInline={4}
        paddingBlock={3}
        wrap="wrap"
        gap={2}
      >
        <Text type="supporting" color="secondary">
          {totalItems > 0 ? (currentPage - 1) * rowsPerPage + 1 : 0} -{' '}
          {Math.min(currentPage * rowsPerPage, totalItems)} dari {totalItems} total entri
        </Text>

        <Pagination
          page={currentPage}
          onChange={(newPage) => updateField('page', newPage)}
          totalPages={totalPages}
          totalItems={totalItems}
          pageSize={rowsPerPage}
          variant="pages"
          size="sm"
        />
      </HStack>
    </Card>
  );
}
