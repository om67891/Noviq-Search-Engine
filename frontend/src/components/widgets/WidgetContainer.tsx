import React from 'react';
import { WidgetData } from '@/types/search';
import { WeatherWidget } from './WeatherWidget';
import { FinanceWidget } from './FinanceWidget';

export function WidgetContainer({ widget }: { widget?: WidgetData }) {
  if (!widget) return null;

  switch (widget.type) {
    case 'weather':
      return <WeatherWidget data={widget.data} />;
    case 'finance':
      return <FinanceWidget data={widget.data} />;
    default:
      return null;
  }
}
