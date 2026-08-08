import { OpenAPIHono } from '@hono/zod-openapi';
import { cors } from 'hono/cors';
import {
  getSummaryRoute,
  getProvincesRoute,
  getRegenciesRoute,
  getClusterProfilesRoute,
  getAiReportRoute,
} from './api.schema';
import { SummaryController } from '../controllers/SummaryController';
import { ProvinceController } from '../controllers/ProvinceController';
import { RegencyController } from '../controllers/RegencyController';
import { ClusterProfileController } from '../controllers/ClusterProfileController';
import { AiReportController } from '../controllers/AiReportController';

type Env = {
  Bindings: {
    DB: D1Database;
  };
};

const api = new OpenAPIHono<{ Bindings: Env['Bindings'] }>();

// Enable CORS for API routes
api.use('/*', cors());

api.openapi(getSummaryRoute, SummaryController.getSummary);
api.openapi(getProvincesRoute, ProvinceController.getAll);
api.openapi(getRegenciesRoute, RegencyController.getPaginated);
api.openapi(getClusterProfilesRoute, ClusterProfileController.getProfiles);
api.openapi(getAiReportRoute, AiReportController.getReport);

// Expose the OpenAPI documentation
api.doc('/doc', {
  openapi: '3.0.0',
  info: {
    version: '1.0.0',
    title: 'SIMKOPDES API Services',
    description: 'API services for SIMKOPDES MLOps and dashboard metrics',
  },
});

export default api;
