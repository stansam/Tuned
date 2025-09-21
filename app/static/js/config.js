(function(global) {
  'use strict';
  
  const ENVIRONMENTS = {
    development: {
      API_BASE_URL: 'http://api.tunedessays.com:5000',
      APP_BASE_URL: 'http://app.tunedessays.com:5000',
      ADMIN_BASE_URL: 'http://admin.tunedessays.com:5000',
      DEBUG: true
    },
    production: {
      API_BASE_URL: 'https://api.tunedessays.com',
      APP_BASE_URL: 'https://app.tunedessays.com',
      ADMIN_BASE_URL: 'https://admin.tunedessays.com',
      DEBUG: false
    }
  };
  
  const getEnvironment = function() {
    const hostname = window.location.hostname;
    if (hostname.includes('localhost') || hostname.includes('127.0.0.1') || hostname.includes('tunedessays.com') && window.location.port === '5000') {
      return 'development';
    }
    return 'production';
  };
  
  const CONFIG = ENVIRONMENTS[getEnvironment()];
  
  global.AppConfig = CONFIG;
  
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
  }
  
})(typeof window !== 'undefined' ? window : this);