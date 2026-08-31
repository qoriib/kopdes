import { Card } from '@astryxdesign/core/Card';
import { HStack, VStack } from '@astryxdesign/core/Layout';
import { Heading, Text } from '@astryxdesign/core/Text';
import { Divider } from '@astryxdesign/core/Divider';
import { Cpu } from 'lucide-react';
import type { SummaryData } from '@/types';

interface ModelPerformanceProps {
  summary: SummaryData | null;
}

export function ModelPerformance({ summary }: ModelPerformanceProps) {
  const metrics = summary?.metrics;

  return (
    <Card padding={5}>
      <VStack gap={4}>
        <HStack align="center" gap={2}>
          <Cpu size={18} />
          <Heading level={3}>Kinerja Model ML</Heading>
        </HStack>

        <VStack gap={2}>
          <HStack justify="between" align="center">
            <Text type="body" color="secondary">
              Silhouette Score
            </Text>
            <Text type="body" weight="semibold">
              {metrics?.silhouette_score || '0.0'}
            </Text>
          </HStack>
          <Divider />

          <HStack justify="between" align="center">
            <Text type="body" color="secondary">
              Calinski-Harabasz Index
            </Text>
            <Text type="body" weight="semibold">
              {metrics?.calinski_harabasz_index || '0.0'}
            </Text>
          </HStack>
          <Divider />

          <HStack justify="between" align="center">
            <Text type="body" color="secondary">
              Davies-Bouldin Index
            </Text>
            <Text type="body" weight="semibold">
              {metrics?.davies_bouldin_index || '0.0'}
            </Text>
          </HStack>
          <Divider />

          <HStack justify="between" align="center">
            <Text type="body" color="secondary">
              Jumlah Klaster Terbentuk (K)
            </Text>
            <Text type="body" weight="semibold">
              {metrics?.number_of_clusters || '3'} Klaster
            </Text>
          </HStack>
          <Divider />

          <HStack justify="between" align="center">
            <Text type="body" color="secondary">
              Algoritma Terbaik
            </Text>
            <Text type="body" weight="semibold">
              {metrics?.best_algorithm || 'Agglomerative Clustering'}
            </Text>
          </HStack>
        </VStack>
      </VStack>
    </Card>
  );
}
