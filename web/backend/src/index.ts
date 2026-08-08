import { Hono } from 'hono';
import api from './routes/api';

type Env = {
  Bindings: {
    DB: D1Database;
  };
};

const app = new Hono<{ Bindings: Env['Bindings'] }>();

app.get('/', (c) => {
  return c.text('SIMKOPDES API Services is online!');
});

// Mount API routes
app.route('/api', api);

export default app;
