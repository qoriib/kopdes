import { z, createRoute } from '@hono/zod-openapi';

// -------------------------------------------------------------
// Request Schemas (Query parameters)
// -------------------------------------------------------------
export const RegencyQuerySchema = z.object({
  province_id: z.string().optional().openapi({
    param: { name: 'province_id', in: 'query' },
    example: '1',
    description: 'Filter by Province ID'
  }),
  cluster_label: z.string().optional().openapi({
    param: { name: 'cluster_label', in: 'query' },
    example: '2',
    description: 'Filter by Cluster Label (0, 1, 2)'
  }),
  search: z.string().optional().openapi({
    param: { name: 'search', in: 'query' },
    example: 'Nganjuk',
    description: 'Search regency by name'
  }),
  page: z.string().optional().openapi({
    param: { name: 'page', in: 'query' },
    example: '1',
    description: 'Page number for pagination'
  }),
  limit: z.string().optional().openapi({
    param: { name: 'limit', in: 'query' },
    example: '10',
    description: 'Limit size of paginated items'
  }),
});

// -------------------------------------------------------------
// Response Body Schemas
// -------------------------------------------------------------
export const SummaryResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    total_provinces: z.number(),
    total_regencies: z.number(),
    total_koperasi: z.number(),
    total_nib: z.number(),
    total_npwp: z.number(),
    total_rat: z.number(),
    total_nilai_transaksi: z.number(),
    metrics: z.record(z.string(), z.string())
  })
}).openapi('SummaryResponse');

export const ProvinceRowSchema = z.object({
  id: z.number(),
  province_name: z.string(),
  jumlah_koperasi: z.number(),
  koperasi_nib: z.number(),
  koperasi_npwp: z.number(),
  koperasi_rat: z.number()
}).openapi('ProvinceRow');

export const ProvincesResponseSchema = z.object({
  success: z.boolean(),
  data: z.array(ProvinceRowSchema)
}).openapi('ProvincesResponse');

export const RegencyRowSchema = z.object({
  id: z.number(),
  province_id: z.number(),
  regency_name: z.string(),
  jumlah_koperasi: z.number(),
  koperasi_nib: z.number(),
  koperasi_npwp: z.number(),
  koperasi_rat: z.number(),
  nilai_transaksi: z.number(),
  cluster_label: z.number(),
  latitude: z.number().optional(),
  longitude: z.number().optional(),
  province_name: z.string().optional()
}).openapi('RegencyRow');

export const RegenciesResponseSchema = z.object({
  success: z.boolean(),
  data: z.array(RegencyRowSchema),
  pagination: z.object({
    page: z.number(),
    limit: z.number(),
    total: z.number(),
    total_pages: z.number()
  })
}).openapi('RegenciesResponse');

export const ClusterProfileRowSchema = z.object({
  cluster_label: z.number(),
  count: z.number(),
  avg_koperasi: z.number(),
  avg_nib: z.number(),
  avg_npwp: z.number(),
  avg_rat: z.number(),
  avg_nilai_transaksi: z.number()
}).openapi('ClusterProfileRow');

export const ClusterProfilesResponseSchema = z.object({
  success: z.boolean(),
  data: z.array(ClusterProfileRowSchema)
}).openapi('ClusterProfilesResponse');

export const AiReportResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    report_text: z.string(),
    labels: z.record(z.string(), z.any())
  })
}).openapi('AiReportResponse');

// -------------------------------------------------------------
// Route Declarations
// -------------------------------------------------------------
export const getSummaryRoute = createRoute({
  method: 'get',
  path: '/summary',
  responses: {
    200: {
      content: {
        'application/json': {
          schema: SummaryResponseSchema,
        },
      },
      description: 'Retrieve summary statistics and metrics',
    },
  },
});

export const getProvincesRoute = createRoute({
  method: 'get',
  path: '/provinces',
  responses: {
    200: {
      content: {
        'application/json': {
          schema: ProvincesResponseSchema,
        },
      },
      description: 'Retrieve all provinces list',
    },
  },
});

export const getRegenciesRoute = createRoute({
  method: 'get',
  path: '/regencies',
  request: {
    query: RegencyQuerySchema,
  },
  responses: {
    200: {
      content: {
        'application/json': {
          schema: RegenciesResponseSchema,
        },
      },
      description: 'Retrieve paginated and filtered regencies list',
    },
  },
});

export const getClusterProfilesRoute = createRoute({
  method: 'get',
  path: '/cluster-profiles',
  responses: {
    200: {
      content: {
        'application/json': {
          schema: ClusterProfilesResponseSchema,
        },
      },
      description: 'Retrieve cluster profile aggregate statistics',
    },
  },
});

export const getAiReportRoute = createRoute({
  method: 'get',
  path: '/ai-report',
  responses: {
    200: {
      content: {
        'application/json': {
          schema: AiReportResponseSchema,
        },
      },
      description: 'Retrieve latest generated AI Interpretation report',
    },
  },
});
