// Fluxline Application Configuration

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// Build WebSocket URL based on HTTP API URL to ensure environments align
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 
  API_BASE_URL.replace(/^http/, 'ws');
