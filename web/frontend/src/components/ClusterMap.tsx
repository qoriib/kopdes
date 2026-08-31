import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { Card } from '@astryxdesign/core/Card';
import { HStack, VStack } from '@astryxdesign/core/Layout';
import { Heading, Text } from '@astryxdesign/core/Text';
import { StatusDot, type StatusDotVariant } from '@astryxdesign/core/StatusDot';
import { Map as MapIcon } from 'lucide-react';
import type { Regency } from '@/types';

interface ClusterMapProps {
  regencies: Regency[];
  labels?: Record<string, unknown>;
}

// Palet warna klaster selaras dengan tema semantik Astryx
const PALET_WARNA_KLASTER = [
  '#0064E0', // accent / blue
  '#0D8626', // success / green
  '#E3193B', // error / red
  '#E9AF08', // warning / yellow
  '#7952FF', // purple
  '#0DB7AF', // teal
];

const VARIAN_STATUS_KLASTER: StatusDotVariant[] = [
  'accent',
  'success',
  'error',
  'warning',
  'neutral',
];

export function ClusterMap({ regencies, labels }: ClusterMapProps) {
  return (
    <Card padding={5}>
      <VStack gap={3}>
        <HStack align="center" gap={2}>
          <MapIcon size={20} />
          <Heading level={3}>Peta Sebaran Klaster</Heading>
        </HStack>

        <MapContainer
          center={[-2.5489, 118.0149]}
          zoom={5}
          scrollWheelZoom={false}
          style={{ height: 420, width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {regencies.map((wilayah) => {
            if (!wilayah.latitude || !wilayah.longitude) return null;
            const clusterKey = wilayah.cluster_label.toString();
            const rawLabel = labels?.[clusterKey];
            const namaLabel =
              typeof rawLabel === 'object' && rawLabel !== null
                ? (rawLabel as { label_name?: string }).label_name || `Klaster ${clusterKey}`
                : String(rawLabel || `Klaster ${clusterKey}`);
            const warnaMarker =
              PALET_WARNA_KLASTER[wilayah.cluster_label % PALET_WARNA_KLASTER.length];

            return (
              <CircleMarker
                key={wilayah.id}
                center={[wilayah.latitude, wilayah.longitude]}
                radius={5}
                pathOptions={{
                  fillColor: warnaMarker,
                  color: '#ffffff',
                  weight: 1,
                  fillOpacity: 0.85,
                }}
              >
                <Popup>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <strong style={{ fontSize: '13px' }}>{wilayah.regency_name}</strong>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                      {wilayah.province_name}
                    </span>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: warnaMarker, marginTop: '2px' }}>
                      {namaLabel}
                    </span>
                    <span style={{ fontSize: '11px', marginTop: '4px', borderTop: '1px solid var(--color-border)', paddingTop: '4px' }}>
                      Total Koperasi: <strong>{(wilayah.total_koperasi || 0).toLocaleString('id-ID')}</strong>
                    </span>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>

        {labels && (
          <HStack gap={3} wrap="wrap" align="center">
            {Object.keys(labels).map((key) => {
              const clusterNum = parseInt(key);
              const varian =
                VARIAN_STATUS_KLASTER[clusterNum % VARIAN_STATUS_KLASTER.length];
              const rawLabel = labels[key];
              const judulLabel =
                typeof rawLabel === 'object' && rawLabel !== null
                  ? (rawLabel as { label_name?: string }).label_name || `Klaster ${key}`
                  : String(rawLabel || `Klaster ${key}`);

              return (
                <HStack key={key} align="center" gap={1.5}>
                  <StatusDot variant={varian} label={judulLabel} />
                  <Text type="body">
                    Klaster {key}: {judulLabel}
                  </Text>
                </HStack>
              );
            })}
          </HStack>
        )}
      </VStack>
    </Card>
  );
}
