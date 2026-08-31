import { LayoutFooter, HStack } from '@astryxdesign/core/Layout';
import { Text } from '@astryxdesign/core/Text';
import { IconButton } from '@astryxdesign/core/IconButton';
import { Sun, Moon } from 'lucide-react';

interface FooterProps {
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
}

export function Footer({ theme = 'light', onToggleTheme }: FooterProps) {
  return (
    <LayoutFooter hasDivider>
      <HStack justify="between" align="center" paddingBlock={4} paddingInline={2} wrap="wrap" gap={3}>
        <Text type="supporting" color="secondary">
          &copy; 2026 SIMKOPDES &bull; Sistem Klasterisasi & Intelijen Koperasi Desa Indonesia
        </Text>

        {onToggleTheme && (
          <IconButton
            variant="ghost"
            size="sm"
            label={theme === 'light' ? 'Beralih ke mode gelap' : 'Beralih ke mode terang'}
            tooltip={theme === 'light' ? 'Mode Gelap' : 'Mode Terang'}
            icon={theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
            onClick={onToggleTheme}
          />
        )}
      </HStack>
    </LayoutFooter>
  );
}
