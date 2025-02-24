const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  chainWebpack: config => {
    config.optimization.splitChunks({
      cacheGroups: {
        vendors: {
          name: 'chunk-vendors',
          test: /[\\/]node_modules[\\/]/,
          priority: -10,
          chunks: 'initial'
        },
        common: {
          name: 'chunk-common',
          minChunks: 2,
          priority: -20,
          chunks: 'initial',
          reuseExistingChunk: true
        }
      }
    })
  },
  // Disable source maps in production
  productionSourceMap: false,
  // Configure CSS extraction
  css: {
    extract: true,
    // Disable CSS source maps
    sourceMap: false
  },
  // Configure webpack performance hints
  configureWebpack: {
    performance: {
      hints: false,
      maxEntrypointSize: 512000,
      maxAssetSize: 512000
    }
  }
}); 