import { Card } from '@astryxdesign/core/Card';
import { HStack, VStack } from '@astryxdesign/core/Layout';
import { Heading, Text } from '@astryxdesign/core/Text';
import { StatusDot, type StatusDotVariant } from '@astryxdesign/core/StatusDot';
import { BookmarkCheck } from 'lucide-react';
import type { AIReport } from '@/types';

interface ClusterDefinitionsProps {
  aiReport: AIReport | null;
}

const CLUSTER_STATUS_VARIANTS: StatusDotVariant[] = [
  'accent',
  'success',
  'error',
  'warning',
  'neutral',
];

export function ClusterDefinitions({ aiReport }: ClusterDefinitionsProps) {
  const labels = aiReport?.labels || {};
  const labelKeys = Object.keys(labels);

  if (labelKeys.length === 0) return null;

  return (
    <Card padding={5}>
      <VStack gap={3}>
        <HStack align="center" gap={2}>
          <BookmarkCheck size={18} />
          <Heading level={3}>Karakteristik Klaster</Heading>
        </HStack>

        <VStack gap={2}>
          {labelKeys.map((key) => {
            const clusterLabel = parseInt(key);
            const rawItem = labels[key];
            const isObject = typeof rawItem === 'object' && rawItem !== null;
            const labelName = isObject ? (rawItem as { label_name?: string }).label_name : String(rawItem);
            const description = isObject ? (rawItem as { description?: string }).description : '';
            const statusVariant =
              CLUSTER_STATUS_VARIANTS[clusterLabel % CLUSTER_STATUS_VARIANTS.length];

            return (
              <Card key={key} padding={3}>
                <VStack gap={1}>
                  <HStack align="center" gap={1.5}>
                    <StatusDot variant={statusVariant} label={`Klaster ${key}`} />
                    <Text type="body" weight="semibold">
                      {labelName || `Klaster ${key}`}
                    </Text>
                  </HStack>
                  {description && (
                    <Text type="supporting" color="secondary">
                      {description}
                    </Text>
                  )}
                </VStack>
              </Card>
            );
          })}
        </VStack>
      </VStack>
    </Card>
  );
}
