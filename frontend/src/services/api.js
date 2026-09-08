import axios from 'axios';

// Base API client using relative URL to leverage Vite proxy or fallback to localhost:8000
const API_BASE = '/api';

export const sendChatPrompt = async (prompt, userId = 'employee_user') => {
  try {
    const response = await axios.post(`${API_BASE}/chat`, {
      prompt,
      user_id: userId
    });
    return response.data;
  } catch (error) {
    console.error('API Error sending chat prompt:', error);
    throw error.response?.data || { detail: 'Gateway connection failed.' };
  }
};

export const fetchAdminStats = async (config = {}) => {
  try {
    const response = await axios.get(`${API_BASE}/admin/stats`, config);
    return response.data;
  } catch (error) {
    if (!axios.isCancel(error)) {
      console.error('API Error fetching admin stats:', error);
    }
    throw error;
  }
};

export const fetchAuditLogs = async (limit = 50, decision = null, riskLevel = null, config = {}) => {
  try {
    const params = { limit };
    if (decision) params.decision = decision;
    if (riskLevel) params.risk_level = riskLevel;

    const response = await axios.get(`${API_BASE}/admin/logs`, { ...config, params });
    return response.data;
  } catch (error) {
    if (!axios.isCancel(error)) {
      console.error('API Error fetching audit logs:', error);
    }
    throw error;
  }
};
