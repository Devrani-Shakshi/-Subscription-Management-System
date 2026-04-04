import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChurnScores } from '@/hooks/useChurn';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import type { ChurnScoreEntry, ChurnFilters } from '@/types/company';
import type { Column, FilterConfig } from '@/types';
import {
  PageHeader, StatCard, FilterBar, DataTable, Pagination,
  PageLoader, StatusBadge, ScoreBar, MobileCard,
} from '@/components/ui';
import { ChurnSignalsRow } from './ChurnSignalsRow';

export const ChurnPage: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const [filters, setFilters] = useState<ChurnFilters>({
    page: 1,
    limit: 25,
  });
  const [riskFilter, setRiskFilter] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);

  const minScore = riskFilter === 'high' ? 70 : riskFilter === 'medium' ? 30 : undefined;
  const { data, isLoading } = useChurnScores({
    ...filters,
    min_score: minScore,
  });

  const entries = data?.data ?? [];
  const total = data?.meta?.total ?? entries.length;

  const stats = {
    high: entries.filter((e) => e.risk_level === 'high').length,
    medium: entries.filter((e) => e.risk_level === 'medium').length,
    low: entries.filter((e) => e.risk_level === 'low').length,
  };

  const filterConfigs: FilterConfig[] = [
    {
      key: 'risk_level',
      label: 'Risk Level',
      type: 'select',
      options: [
        { label: 'All', value: '' },
        { label: 'High (≥70)', value: 'high' },
        { label: 'Medium (30-69)', value: 'medium' },
        { label: 'Low (<30)', value: 'low' },
      ],
    },
  ];

  const columns: Column<ChurnScoreEntry>[] = [
    { key: 'customer_name', header: 'Customer', sortable: true },
    { key: 'customer_email', header: 'Email' },
    {
      key: 'plan_name', header: 'Plan',
      render: (row) => row.plan_name ?? <span className="text-gray-600">—</span>,
    },
    {
      key: 'score', header: 'Score', sortable: true,
      render: (row) => <ScoreBar score={row.score} />,
    },
    {
      key: 'risk_level', header: 'Risk',
      render: (row) => <StatusBadge status={row.risk_level} />,
    },
    {
      key: 'signals', header: 'Signals',
      render: (row) => {
        const triggered = row.signals.filter((s) => s.triggered).length;
        return (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(expanded === row.id ? null : row.id);
            }}
            className="text-xs text-violet-400 hover:text-violet-300"
          >
            {triggered}/{row.signals.length} triggered
          </button>
        );
      },
    },
    {
      key: 'actions', header: '', width: '80px',
      render: (row) => (
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/company/customers/${row.customer_id}`); }}
          className="text-xs text-gray-400 hover:text-violet-400 h-8 px-2 rounded-lg
                     hover:bg-violet-500/10 transition-colors"
        >
          View
        </button>
      ),
    },
  ];

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Churn prediction"
        subtitle="Scores updated daily. High risk = score ≥ 70."
      />

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="High Risk" value={stats.high} icon="AlertTriangle" color="rose" />
        <StatCard label="Medium Risk" value={stats.medium} icon="AlertCircle" color="amber" />
        <StatCard label="Low Risk" value={stats.low} icon="CheckCircle" color="teal" />
      </div>

      <FilterBar
        filters={filterConfigs}
        values={{ risk_level: riskFilter }}
        onChange={(_, v) => { setRiskFilter(v); setFilters((f) => ({ ...f, page: 1 })); }}
      />

      {/* Desktop table with expandable signals */}
      <div className="hidden lg:block">
        <DataTable columns={columns} data={entries} />
        {expanded && <ExpandedSignals entries={entries} expandedId={expanded} />}
      </div>

      {/* Mobile cards */}
      {isMobile && (
        <div className="space-y-3 lg:hidden">
          {entries.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No churn data</p>
          ) : entries.map((e) => (
            <div key={e.id}>
              <MobileCard
                title={e.customer_name}
                subtitle={<StatusBadge status={e.risk_level} />}
                onClick={() => setExpanded(expanded === e.id ? null : e.id)}
                fields={[
                  { label: 'Score', value: <ScoreBar score={e.score} /> },
                  { label: 'Plan', value: e.plan_name ?? '—' },
                ]}
                trailing={
                  <button onClick={() => navigate(`/company/customers/${e.customer_id}`)}
                    className="text-xs text-violet-400">View</button>
                }
              />
              {expanded === e.id && <ChurnSignalsRow signals={e.signals} />}
            </div>
          ))}
        </div>
      )}

      {total > filters.limit && (
        <Pagination
          total={total}
          page={filters.page}
          limit={filters.limit}
          onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
          onLimitChange={(l) => setFilters((f) => ({ ...f, limit: l, page: 1 }))}
        />
      )}
    </div>
  );
};

/* Inline expanded signals for desktop */
const ExpandedSignals: React.FC<{ entries: ChurnScoreEntry[]; expandedId: string }> = ({
  entries, expandedId,
}) => {
  const entry = entries.find((e) => e.id === expandedId);
  if (!entry) return null;
  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 -mt-1 mb-4">
      <ChurnSignalsRow signals={entry.signals} />
    </div>
  );
};
