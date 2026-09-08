import React from 'react';
import { Tag } from 'lucide-react';

export default function CategoryChip({ category }) {
  const formatLabel = (cat) => {
    switch (cat) {
      case 'EMAIL_ADDRESS': return 'Email Address';
      case 'PHONE_NUMBER': return 'Phone Number';
      case 'API_KEY': return 'API Key Secret';
      case 'PASSWORD': return 'Password Credential';
      case 'ACCESS_TOKEN': return 'Access Token';
      case 'INTERNAL_EMPLOYEE_ID': return 'Employee ID';
      case 'CONFIDENTIAL_MARKER': return 'Confidential Text';
      case 'DATABASE_CONNECTION': return 'Database URL';
      default: return cat.replace(/_/g, ' ');
    }
  };

  return (
    <span className="category-chip">
      <Tag size={12} />
      {formatLabel(category)}
    </span>
  );
}
