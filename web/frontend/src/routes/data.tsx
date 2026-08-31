import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { z } from 'zod';
import { fetchProvinces, fetchRegencies, fetchAIReport } from '@/api';
import { DataTableSection } from '@/components/DataTableSection';

export const dataSearchSchema = z.object({
  type: z.enum(['regencies', 'provinces']).default('regencies').catch('regencies'),
  search: z.string().default('').catch(''),
  cluster: z.string().default('all').catch('all'),
  date: z.string().default('').catch(''),
  page: z.number().int().positive().default(1).catch(1),
});

export type DataSearch = z.infer<typeof dataSearchSchema>;

export const Route = createFileRoute('/data')({
  validateSearch: (search: Record<string, unknown>): DataSearch => {
    return dataSearchSchema.parse(search);
  },
  loader: async () => {
    const [provinces, regencies, aiReport] = await Promise.all([
      fetchProvinces(),
      fetchRegencies(1000),
      fetchAIReport(),
    ]);

    return {
      provinces,
      regencies,
      aiReport,
    };
  },
  component: DataRouteComponent,
});

function DataRouteComponent() {
  const { provinces, regencies, aiReport } = Route.useLoaderData();
  const searchParams = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });

  const handleUpdateSearch = (updates: Partial<DataSearch>) => {
    navigate({
      search: (prev) => ({
        ...prev,
        ...updates,
      }),
      replace: true,
    });
  };

  return (
    <DataTableSection
      provinces={provinces}
      regencies={regencies}
      aiReport={aiReport}
      searchParams={searchParams}
      onUpdateSearch={handleUpdateSearch}
    />
  );
}
