import { Regency } from '../orm/Regency';

export class RegencyController {
  static async getPaginated(c: any) {
    try {
      const db = c.env.DB;
      const regencyModel = new Regency(db);

      // Access query parameters validated by Zod OpenAPI schema
      const query = c.req.valid('query');
      const provinceId = query?.province_id;
      const clusterLabel = query?.cluster_label;
      const search = query?.search || '';
      const page = parseInt(query?.page || '1');
      const limit = parseInt(query?.limit || '10');
      const offset = (page - 1) * limit;

      const filterOptions = {
        provinceId: provinceId ? parseInt(provinceId) : undefined,
        clusterLabel: clusterLabel ? parseInt(clusterLabel) : undefined,
        search: search || undefined,
      };

      const regencies = await regencyModel.findWithProvince({
        ...filterOptions,
        limit,
        offset,
      });

      const totalCount = await regencyModel.countWithProvince(filterOptions);

      return c.json({
        success: true,
        data: regencies,
        pagination: {
          page,
          limit,
          total: totalCount,
          total_pages: Math.ceil(totalCount / limit),
        },
      });
    } catch (err: any) {
      return c.json({ success: false, error: err.message }, 500);
    }
  }
}
