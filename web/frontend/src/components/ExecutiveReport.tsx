import { Card } from '@astryxdesign/core/Card';
import { HStack, VStack } from '@astryxdesign/core/Layout';
import { Heading, Text } from '@astryxdesign/core/Text';
import { Markdown } from '@astryxdesign/core/Markdown';
import { Sparkles } from 'lucide-react';
import type { AIReport } from '@/types';

interface ExecutiveReportProps {
  aiReport: AIReport | null;
}

export function ExecutiveReport({ aiReport }: ExecutiveReportProps) {
  return (
    <Card padding={5}>
      <VStack gap={4}>
        <HStack align="center" gap={2}>
          <Sparkles size={18} />
          <Heading level={3}>Laporan Eksekutif</Heading>
        </HStack>

        {aiReport?.report_text ? (
          <Markdown density="compact" headingLevelStart={4} autolink="gfm">
            {aiReport.report_text.replace(/\\n/g, '\n')}
          </Markdown>
        ) : (
          <Text type="body" color="secondary">
            Laporan analisis belum tersedia.
          </Text>
        )}
      </VStack>
    </Card>
  );
}
