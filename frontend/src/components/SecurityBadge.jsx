import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

export default function SecurityBadge({ type, value }) {
  if (type === 'decision') {
    if (value === 'ALLOW') {
      return (
        <span className="badge badge-allow">
          <CheckCircle2 size={14} /> ALLOW
        </span>
      );
    }
    return (
      <span className="badge badge-block">
        <ShieldAlert size={14} /> BLOCKED
      </span>
    );
  }

  if (type === 'risk') {
    switch (value) {
      case 'CRITICAL':
        return (
          <span className="badge badge-risk-critical">
            <ShieldAlert size={14} /> CRITICAL
          </span>
        );
      case 'HIGH':
        return (
          <span className="badge badge-risk-high">
            <AlertTriangle size={14} /> HIGH
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="badge badge-risk-medium">
            <AlertTriangle size={14} /> MEDIUM
          </span>
        );
      default:
        return (
          <span className="badge badge-risk-low">
            <Info size={14} /> LOW
          </span>
        );
    }
  }

  return <span className="badge">{value}</span>;
}
