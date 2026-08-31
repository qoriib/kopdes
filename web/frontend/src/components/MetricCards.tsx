import { Grid } from '@astryxdesign/core/Grid';
import { Card } from '@astryxdesign/core/Card';
import { HStack, VStack } from '@astryxdesign/core/Layout';
import { Heading, Text } from '@astryxdesign/core/Text';
import { Building2, CheckCircle2, TrendingUp, Coins } from 'lucide-react';
import type { SummaryData } from '@/types';

interface MetricCardsProps {
  summary: SummaryData | null;
}

export function MetricCards({ summary }: MetricCardsProps) {
  const totalKoperasi = summary?.total_koperasi || 0;
  const totalNib = summary?.total_nib || 0;
  const totalRat = summary?.total_rat || 0;
  const totalTransaksi = summary?.total_nilai_transaksi || 0;

  const nibPercentage = totalKoperasi > 0 ? ((totalNib / totalKoperasi) * 100).toFixed(1) : '0';
  const ratPercentage = totalKoperasi > 0 ? ((totalRat / totalKoperasi) * 100).toFixed(1) : '0';
  const transaksiTriliun = (totalTransaksi / 1e12).toFixed(2);

  const cards = [
    {
      title: 'Total Koperasi',
      value: totalKoperasi.toLocaleString('id-ID'),
      sub: `${summary?.total_provinces || 0} Provinsi / ${summary?.total_regencies || 0} Kab/Kota`,
      icon: Building2,
    },
    {
      title: 'Koperasi NIB',
      value: `${nibPercentage}%`,
      sub: `${totalNib.toLocaleString('id-ID')} unit terdaftar`,
      icon: CheckCircle2,
    },
    {
      title: 'Koperasi RAT Aktif',
      value: `${ratPercentage}%`,
      sub: `${totalRat.toLocaleString('id-ID')} unit aktif RAT`,
      icon: TrendingUp,
    },
    {
      title: 'Total Transaksi',
      value: `Rp ${transaksiTriliun} T`,
      sub: 'Volume usaha teragregasi',
      icon: Coins,
    },
  ];

  return (
    <Grid columns={{ minWidth: 240, max: 4 }} gap={4}>
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <Card key={idx} padding={4}>
            <VStack gap={2}>
              <HStack justify="between" align="center">
                <Text type="label" color="secondary">
                  {card.title}
                </Text>
                <Icon size={16} />
              </HStack>
              <Heading level={2}>{card.value}</Heading>
              <Text type="supporting" color="secondary">
                {card.sub}
              </Text>
            </VStack>
          </Card>
        );
      })}
    </Grid>
  );
}
