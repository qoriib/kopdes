import { createFileRoute } from '@tanstack/react-router';
import { VStack } from '@astryxdesign/core/Layout';
import { Grid, GridSpan } from '@astryxdesign/core/Grid';
import { MetricCards } from '@/components/MetricCards';
import { ClusterMap } from '@/components/ClusterMap';
import { ExecutiveReport } from '@/components/ExecutiveReport';
import { ModelPerformance } from '@/components/ModelPerformance';
import { ClusterDefinitions } from '@/components/ClusterDefinitions';
import { fetchSummary, fetchProvinces, fetchRegencies, fetchAIReport } from '@/api';

export const Route = createFileRoute('/')({
  loader: async () => {
    const [summary, provinces, regencies, aiReport] = await Promise.all([
      fetchSummary(),
      fetchProvinces(),
      fetchRegencies(1000),
      fetchAIReport(),
    ]);

    return {
      summary,
      provinces,
      regencies,
      aiReport,
    };
  },
  component: HomeComponent,
});

function HomeComponent() {
  const { summary, regencies, aiReport } = Route.useLoaderData();

  return (
    <VStack gap={5}>
      {/* 1. Kartu Ringkasan Metrik Utama */}
      <MetricCards summary={summary} />

      {/* 2. Peta Sebaran Klaster Interaktif */}
      <ClusterMap regencies={regencies} labels={aiReport?.labels} />

      {/* 3. Laporan Eksekutif & Kinerja Model */}
      <Grid columns={{ minWidth: 320, max: 3 }} gap={4}>
        <GridSpan columns={2}>
          <ExecutiveReport aiReport={aiReport} />
        </GridSpan>

        <VStack gap={4}>
          <ModelPerformance summary={summary} />
          <ClusterDefinitions aiReport={aiReport} />
        </VStack>
      </Grid>
    </VStack>
  );
}
