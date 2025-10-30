const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8002',
      changeOrigin: true,
      secure: false,
      logLevel: 'info',
      onError: (err, req, res) => {
        console.log('Proxy error:', err.message);
      }
    })
  );
};