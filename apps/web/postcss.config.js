// =============================================================================
// POSTCSS CONFIGURATION
// =============================================================================

module.exports = {
  plugins: {
    'tailwindcss': {},
    'autoprefixer': {},
    'postcss-preset-env': {
      stage: 3,
      features: {
        'nesting-rules': true,
      },
    },
    ...(process.env.NODE_ENV === 'production' ? {
      'cssnano': {
        preset: 'default',
      },
    } : {}),
  },
};
