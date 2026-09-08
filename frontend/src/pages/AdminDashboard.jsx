import React, { useState, useEffect, useRef, useCallback } from 'react';
import { fetchAdminStats, fetchAuditLogs } from '../services/api';
import SecurityBadge from '../components/SecurityBadge';
import CategoryChip from '../components/CategoryChip';
import {
  ShieldAlert, ShieldCheck, Activity, RefreshCw,
  Search, Filter, Clock, Circle, AlertTriangle, Lock, Wifi, WifiOff
} from 'lucide-react';

const POLL_INTERVAL_MS = 3000;

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [connectionError, setConnectionError] = useState(false);
  const [filterDecision, setFilterDecision] = useState('');
  const [filterRisk, setFilterRisk] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [secondsAgo, setSecondsAgo] = useState(0);

  const requestControllerRef = useRef(null);
  const requestSequenceRef = useRef(0);

  const fetchData = useCallback(async () => {
    requestControllerRef.current?.abort();
    const controller = new AbortController();
    const requestSequence = ++requestSequenceRef.current;
    requestControllerRef.current = controller;
    setIsRefreshing(true);

    try {
      const [statsData, logsData] = await Promise.all([
        fetchAdminStats({ signal: controller.signal }),
        fetchAuditLogs(50, filterDecision || null, filterRisk || null, { signal: controller.signal })
      ]);
      if (controller.signal.aborted || requestSequence !== requestSequenceRef.current) return;

      setStats(statsData);
      setLogs(logsData);
      setLastUpdated(new Date());
      setSecondsAgo(0);
      setConnectionError(false);
    } catch (err) {
      if (controller.signal.aborted || requestSequence !== requestSequenceRef.current) return;

      console.error('Dashboard fetch error:', err);
      setConnectionError(true);
      // Keep existing data on error — do not wipe state
    } finally {
      if (requestSequence === requestSequenceRef.current) {
        setInitialLoading(false);
        setIsRefreshing(false);
      }
    }
  }, [filterDecision, filterRisk]);

  // Polling setup — single interval, cleaned up on unmount
  useEffect(() => {
    fetchData();

    const pollInterval = window.setInterval(() => {
      fetchData();
    }, POLL_INTERVAL_MS);

    // Seconds-since-update tick
    const updatedAtTick = window.setInterval(() => {
      setSecondsAgo(prev => prev + 1);
    }, 1000);

    return () => {
      window.clearInterval(pollInterval);
      window.clearInterval(updatedAtTick);
      requestSequenceRef.current += 1;
      requestControllerRef.current?.abort();
    };
  }, [fetchData]);

  const handleManualRefresh = () => {
    fetchData();
  };

  const formatSecondsAgo = (s) => {
    if (s <= 1) return 'just now';
    if (s < 60) return `${s}s ago`;
    return `${Math.floor(s / 60)}m ago`;
  };

  const filteredLogs = logs.filter(log => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      log.user_id?.toLowerCase().includes(q) ||
      log.prompt_snippet?.toLowerCase().includes(q) ||
      log.policy_decision?.toLowerCase().includes(q) ||
      log.risk_level?.toLowerCase().includes(q)
    );
  });

  const totalReq = stats?.summary?.total_requests ?? 0;
  const allowedReq = stats?.summary?.allowed_requests ?? 0;
  const blockedReq = stats?.summary?.blocked_requests ?? 0;
  const blockRate = stats?.summary?.block_rate_percent ?? 0;

  return (
    <div className="admin-page">
      {/* ── Page Header ───────────────────────────────────────── */}
      <div className="admin-page-header">
        <div className="admin-header-left">
          <h1 className="admin-title">Security Administrator Dashboard</h1>
          <p className="admin-desc">
            Gateway monitoring, data-loss analytics, and security audit logs.
          </p>
        </div>

        <div className="admin-header-right">
          {/* Live status pill */}
          <div className={`live-status-pill ${connectionError ? 'live-status-error' : 'live-status-ok'}`}>
            {connectionError ? (
              <>
                <WifiOff size={12} />
                <span>Connection lost</span>
              </>
            ) : (
              <>
                <Circle size={8} className="live-dot" />
                <span>Live</span>
                {lastUpdated && (
                  <span className="live-updated">· {formatSecondsAgo(secondsAgo)}</span>
                )}
              </>
            )}
          </div>

          <button
            className="btn-refresh"
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            title="Refresh now"
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
            <span>{isRefreshing ? 'Refreshing' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* ── KPI Cards ─────────────────────────────────────────── */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon kpi-icon-total">
            <Activity size={20} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Total Requests</span>
            <span className="kpi-value">{totalReq.toLocaleString()}</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon kpi-icon-allow">
            <ShieldCheck size={20} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Allowed Requests</span>
            <span className="kpi-value kpi-value-allow">{allowedReq.toLocaleString()}</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon kpi-icon-block">
            <ShieldAlert size={20} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Blocked Requests</span>
            <span className="kpi-value kpi-value-block">{blockedReq.toLocaleString()}</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon kpi-icon-rate">
            <Filter size={20} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Block Rate</span>
            <span className="kpi-value">{blockRate}%</span>
          </div>
        </div>
      </div>

      {/* ── Analytics Row ─────────────────────────────────────── */}
      <div className="analytics-row">
        {/* Detected Categories */}
        <div className="analytics-panel">
          <div className="panel-heading">
            <Lock size={14} className="panel-icon-danger" />
            <span>Detected Sensitive Categories</span>
          </div>

          {stats?.category_counts && Object.keys(stats.category_counts).length > 0 ? (
            <div className="cat-bars">
              {Object.entries(stats.category_counts)
                .sort((a, b) => b[1] - a[1])
                .map(([cat, count], idx) => {
                  const pct = totalReq > 0 ? Math.min(100, (count / totalReq) * 100) : 0;
                  return (
                    <div key={idx} className="cat-bar-row">
                      <div className="cat-bar-labels">
                        <span className="cat-name">{cat.replace(/_/g, ' ')}</span>
                        <span className="cat-count">{count}</span>
                      </div>
                      <div className="cat-track">
                        <div className="cat-fill" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
            </div>
          ) : (
            <p className="panel-empty">No sensitive categories detected yet.</p>
          )}
        </div>

        {/* Risk Distribution */}
        <div className="analytics-panel">
          <div className="panel-heading">
            <AlertTriangle size={14} className="panel-icon-warning" />
            <span>Risk Level Distribution</span>
          </div>

          <div className="risk-distribution">
            {[
              { key: 'CRITICAL', cls: 'risk-critical' },
              { key: 'HIGH',     cls: 'risk-high' },
              { key: 'MEDIUM',   cls: 'risk-medium' },
              { key: 'LOW',      cls: 'risk-low' },
            ].map(({ key, cls }) => (
              <div key={key} className={`risk-tile ${cls}`}>
                <span className="risk-tile-label">{key}</span>
                <span className="risk-tile-val">
                  {stats?.risk_level_counts?.[key] ?? 0}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Audit Log Table ───────────────────────────────────── */}
      <div className="audit-card">
        <div className="audit-card-header">
          <div className="audit-header-left">
            <h3 className="audit-title">Security Audit Log</h3>
            <span className="audit-count">
              {filteredLogs.length} {filteredLogs.length === 1 ? 'record' : 'records'}
            </span>
          </div>

          <div className="audit-filters">
            <div className="search-field">
              <Search size={13} className="search-icon" />
              <input
                type="text"
                placeholder="Search by user or prompt…"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>

            <select
              className="filter-select"
              value={filterDecision}
              onChange={e => setFilterDecision(e.target.value)}
            >
              <option value="">All Decisions</option>
              <option value="ALLOW">ALLOW</option>
              <option value="BLOCK">BLOCK</option>
            </select>

            <select
              className="filter-select"
              value={filterRisk}
              onChange={e => setFilterRisk(e.target.value)}
            >
              <option value="">All Risk Levels</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>

        <div className="audit-table-wrap">
          {initialLoading ? (
            <div className="audit-loading">
              <div className="pulse-spinner" />
              <span>Loading audit records…</span>
            </div>
          ) : (
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Employee</th>
                  <th>Redacted Prompt</th>
                  <th>Categories</th>
                  <th>Risk</th>
                  <th>Decision</th>
                  <th>LLM Called</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.length > 0 ? (
                  filteredLogs.map(log => {
                    let cats = [];
                    try { cats = JSON.parse(log.detected_entities); } catch {}
                    return (
                      <tr key={log.id}>
                        <td className="td-time">
                          {new Date(log.timestamp).toLocaleTimeString([], {
                            hour: '2-digit', minute: '2-digit', second: '2-digit'
                          })}
                        </td>
                        <td className="td-user">{log.user_id}</td>
                        <td className="td-prompt" title={log.prompt_snippet}>
                          <code>{log.prompt_snippet}</code>
                        </td>
                        <td>
                          <div className="chips-row">
                            {cats.length > 0
                              ? cats.map((c, i) => <CategoryChip key={i} category={c} />)
                              : <span className="td-none">—</span>}
                          </div>
                        </td>
                        <td><SecurityBadge type="risk" value={log.risk_level} /></td>
                        <td><SecurityBadge type="decision" value={log.policy_decision} /></td>
                        <td className="td-llm">
                          {log.llm_called
                            ? <span className="llm-yes">✓ Yes</span>
                            : <span className="llm-no">✕ No</span>}
                        </td>
                        <td className="td-latency">{log.latency_ms} ms</td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={8} className="td-empty">
                      No audit records found matching the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
