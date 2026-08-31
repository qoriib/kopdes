import { useState, useEffect } from 'react';
import { createRootRoute, Outlet, useLocation, useNavigate } from '@tanstack/react-router';
import { Theme } from '@astryxdesign/core/theme';
import { neutralTheme } from '@astryxdesign/theme-neutral/built';
import { AppShell } from '@astryxdesign/core/AppShell';
import { TopNav, TopNavHeading, TopNavItem } from '@astryxdesign/core/TopNav';
import { Layout, LayoutHeader, LayoutContent } from '@astryxdesign/core/Layout';
import { VStack } from '@astryxdesign/core/Layout';
import { Card } from '@astryxdesign/core/Card';
import { Heading, Text } from '@astryxdesign/core/Text';
import { Spinner } from '@astryxdesign/core/Spinner';
import { Button } from '@astryxdesign/core/Button';
import { StatusDot } from '@astryxdesign/core/StatusDot';
import { Home as HomeIcon, Database as DatabaseIcon } from 'lucide-react';
import { Footer } from '@/components/Footer';

export const Route = createRootRoute({
  component: RootComponent,
  pendingComponent: RootPendingComponent,
  errorComponent: RootErrorComponent,
});

function RootComponent() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  return (
    <Theme theme={neutralTheme} mode={theme}>
      <AppShell
        height="auto"
        variant="surface"
      >
        <Layout
          contentWidth={1280}
          header={
            <LayoutHeader>
              <TopNav
                label="Navigasi Utama SIMKOPDES"
                heading={
                  <TopNavHeading
                    heading="SIMKOPDES"
                    subheading="Sistem Analisis & Klasterisasi Koperasi Desa"
                  />
                }
                endContent={
                  <>
                    <TopNavItem
                      label="Beranda"
                      icon={<HomeIcon size={16} />}
                      isSelected={location.pathname === '/'}
                      onClick={() => navigate({ to: '/' })}
                    />
                    <TopNavItem
                      label="Basis Data"
                      icon={<DatabaseIcon size={16} />}
                      isSelected={location.pathname.startsWith('/data')}
                      onClick={() =>
                        navigate({
                          to: '/data',
                          search: {
                            type: 'regencies',
                            search: '',
                            cluster: 'all',
                            date: '',
                            page: 1,
                          },
                        })
                      }
                    />
                  </>
                }
              />
            </LayoutHeader>
          }
          content={
            <LayoutContent>
              <VStack>
                <Outlet />
                <Footer
                  theme={theme}
                  onToggleTheme={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                />
              </VStack>
            </LayoutContent>
          }
        />
      </AppShell>
    </Theme>
  );
}

function RootPendingComponent() {
  return (
    <Layout
      height="auto"
      contentWidth={800}
      content={
        <LayoutContent isScrollable={false} padding={8}>
          <VStack align="center" justify="center" gap={3} height={320}>
            <Spinner size="lg" label="Memuat SIMKOPDES..." />
            <Text type="supporting" color="secondary">
              Memuat data analisis dan klasterisasi wilayah...
            </Text>
          </VStack>
        </LayoutContent>
      }
    />
  );
}

function RootErrorComponent({ error, reset }: { error: unknown; reset: () => void }) {
  const errorMessage =
    error instanceof Error ? error.message : 'Terjadi kesalahan sistem saat memuat halaman.';

  return (
    <Layout
      height="auto"
      contentWidth={640}
      content={
        <LayoutContent isScrollable={false} padding={8}>
          <Card padding={6}>
            <VStack align="center" gap={4}>
              <StatusDot variant="error" label="Kesalahan Sistem" isPulsing />
              <Heading level={3}>Gagal Memuat Halaman</Heading>
              <Text type="body" color="secondary">
                {errorMessage}
              </Text>
              <Button variant="primary" label="Coba Lagi" onClick={reset} />
            </VStack>
          </Card>
        </LayoutContent>
      }
    />
  );
}
